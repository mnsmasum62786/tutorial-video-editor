// On-device OCR (Apple Vision) that finds sensitive tokens and prints their boxes.
// usage: ocr_redact <list.txt> [redact_terms.json]   (one image path per line)
// redact_terms.json: {"client_terms": ["acmefitness", "stape.io"], "names": ["John Smith"]}
//   client_terms — domains / brand slugs: any URL, domain or slug containing one is blurred
//   names        — people to hide (first name, last name or both); at the start of a line
//                  (WhatsApp list, chat header) the photo left of it and the line under it go too
// output: one JSON line per image: {"f": path, "m": [[x, y, w, h, "kind", "text"], ...]}
// boxes are normalised to the image, origin top-left.
import Foundation
import Vision
import AppKit

var terms: [String] = []
var names: [String] = []
if CommandLine.arguments.count > 2,
   let d = FileManager.default.contents(atPath: CommandLine.arguments[2]),
   let j = try? JSONSerialization.jsonObject(with: d) as? [String: Any] {
    terms = (j["client_terms"] as? [String]) ?? []
    names = (j["names"] as? [String]) ?? []
}
func esc(_ s: String) -> String { NSRegularExpression.escapedPattern(for: s) }
var patterns: [(String, String)] = []
if !names.isEmpty {
    // each full name, and each part of it on its own ("John", "Smith")
    var alts = Set<String>()
    for n in names {
        alts.insert(n.split(separator: " ").map { esc(String($0)) }.joined(separator: "\\s+"))
        for part in n.split(separator: " ") where part.count > 2 { alts.insert(esc(String(part))) }
    }
    let sorted = alts.sorted { $0.count > $1.count }   // longest first: the full name wins
    patterns.append(("name", "(?i)\\b(?:" + sorted.joined(separator: "|") + ")\\b"))
}
patterns += [
    ("gtm", #"GTM-[A-Z0-9]{5,9}"#),
    ("gtag", #"\b(?:G|GT|DC|AW)-[A-Z0-9]{6,14}(?:/[A-Za-z0-9_\-]{4,})?"#),
    ("ads_cid", #"\b\d{3}-\d{3}-\d{4}\b"#),
    ("uuid", #"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{8,12}"#),
    ("tiktok", #"\bC[A-Z0-9]{17,21}\b"#),
    ("token", #"\b(?:EAA|sk-|sk_live_|sk_test_|pk_live_|pk_test_|rk_live_|whsec_|AKIA|ya29\.|AIza|ghp_|gho_|github_pat_|xox[abprs]-|shpat_|shpss_|eyJ)[A-Za-z0-9_\-\.]{12,}"#),
    // a value right after a credential label — catches short IDs (LinkedIn partner, UET, Pinterest)
    ("labelled", #"(?i)\b(?:partner|pixel|tag|measurement|container|account|customer|property|conversion|dataset|app|client|merchant|advertiser|business|ad\s*account)\s*id\s*[:=#]?\s*[A-Za-z0-9_\-\.]{5,}|\b(?:api[\s_-]*key|access[\s_-]*token|secret|password|app[\s_-]*secret)\s*[:=]\s*\S{4,}"#),
    ("ip", #"\b(?:\d{1,3}\.){3}\d{1,3}\b"#),
    ("longtoken", #"\b[A-Za-z0-9_\-]{28,}\b"#),
    ("number", #"(?<![\w.])\+?\d[\d \-]{7,}\d(?![\w])"#),
    ("email", #"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+\.[A-Za-z0-9.\-]+"#),
    ("url", #"(?i)https?://[^\s)\]>"']+"#),
]
if !terms.isEmpty {
    let alt = terms.map { esc($0) }.joined(separator: "|")
    // before the generic URL rule, so bare domains and slugs are caught too
    patterns.insert(("client_url", "(?i)(?:https?://)?[A-Za-z0-9.\\-]*(?:" + alt + ")[A-Za-z0-9.\\-]*(?:/[^\\s)\\]>\"']*)?"), at: patterns.count - 1)
}
let regexes = patterns.map { ($0.0, try! NSRegularExpression(pattern: $0.1)) }

func scan(_ path: String) -> [[Any]] {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { return [] }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = false
    req.minimumTextHeight = 0.006
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    try? handler.perform([req])
    var out: [[Any]] = []
    for obs in req.results ?? [] {
        // a line cut by the top or bottom edge cannot be read reliably by OCR, but a viewer may
        // still make out half of it: blur the whole partial line
        let ob = obs.boundingBox
        if ob.minY < 0.012 || ob.maxY > 0.988 {
            let c = obs.topCandidates(1).first
            let t = c?.string ?? ""
            // ignore a leading icon OCR reads as a character ("1 Conversation History")
            let body = t.replacingOccurrences(of: #"^\S{1,2}\s"#, with: "", options: .regularExpression)
            let idLike = body.rangeOfCharacter(from: CharacterSet(charactersIn: "0123456789-./@")) != nil
            if idLike || (c?.confidence ?? 0) < 0.5 {
                out.append([ob.minX, 1 - ob.maxY, ob.width, ob.height, "edge", t])
            }
            continue
        }
        guard let cand = obs.topCandidates(1).first else { continue }
        let s = cand.string
        let ns = s as NSString
        var taken: [NSRange] = []
        for (kind, re) in regexes {
            for m in re.matches(in: s, range: NSRange(location: 0, length: ns.length)) {
                if taken.contains(where: { NSIntersectionRange($0, m.range).length > 0 }) { continue }
                // plain numbers: only IDs (9+ digits) — skip prices, dates, short counts
                let txt = ns.substring(with: m.range)
                if kind == "number" && txt.filter({ $0.isNumber }).count < 9 { continue }
                if kind == "longtoken" && txt.filter({ $0.isNumber }).count < 4 { continue }
                // the client name alone is not a URL; a domain, path or slug is
                if kind == "client_url" && !txt.contains(".") && !txt.contains("/") && !txt.contains("-") { continue }
                taken.append(m.range)
                guard let r = Range(m.range, in: s),
                      let bb = try? cand.boundingBox(for: r)?.boundingBox else { continue }
                if kind == "name" && m.range.location == 0 {
                    // WhatsApp list / chat header: the profile photo sits left of the name and the
                    // message preview under it — cover all three
                    let h = bb.height
                    let hx = h * Double(cg.height) / Double(cg.width)   // the same length in width units
                    out.append([bb.minX - 3.8 * hx, 1 - bb.maxY - 1.2 * h, bb.width + 3.8 * hx, bb.height + 2.6 * h, kind, txt])
                } else if ob.height > bb.height * 1.6 || bb.height > ob.height * 1.6 {
                    // the observation spans several lines (a wrapped table cell): the box Vision
                    // returns for the match can sit on the wrong line, so cover the whole block
                    out.append([ob.minX, 1 - ob.maxY, ob.width, ob.height, kind, txt])
                } else {
                    out.append([bb.minX, 1 - bb.maxY, bb.width, bb.height, kind, txt])
                }
            }
        }
    }
    return out
}

let list = try! String(contentsOfFile: CommandLine.arguments[1], encoding: .utf8)  // image paths, one per line
for path in list.split(separator: "\n").map(String.init) where !path.isEmpty {
    let m = scan(path)
    let data = try! JSONSerialization.data(withJSONObject: ["f": path, "m": m])
    print(String(data: data, encoding: .utf8)!)
    fflush(stdout)
}
