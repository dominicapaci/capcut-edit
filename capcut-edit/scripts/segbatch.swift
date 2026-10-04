import Foundation
import Vision
import CoreImage
// segbatch <framesDir> <outDir> : person mask (8-bit PNG, frame size) for every frame, in order
let a = CommandLine.arguments
let inDir = URL(fileURLWithPath: a[1]), outDir = URL(fileURLWithPath: a[2])
try FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)
let files = try FileManager.default.contentsOfDirectory(atPath: a[1]).filter{$0.hasSuffix(".jpg") || $0.hasSuffix(".png")}.sorted()
let ctx = CIContext()
let cs = CGColorSpace(name: CGColorSpace.linearGray)!
let req = VNGeneratePersonSegmentationRequest()
req.qualityLevel = .accurate
req.outputPixelFormat = kCVPixelFormatType_OneComponent8
var n = 0
for f in files {
    autoreleasepool {
        let ci = CIImage(contentsOf: inDir.appendingPathComponent(f))!
        let h = VNImageRequestHandler(ciImage: ci, options: [:])
        do { try h.perform([req]) } catch { print("fail", f); return }
        let mask = CIImage(cvPixelBuffer: req.results!.first!.pixelBuffer)
        let sx = ci.extent.width / mask.extent.width, sy = ci.extent.height / mask.extent.height
        let scaled = mask.transformed(by: CGAffineTransform(scaleX: sx, y: sy))
        let out = outDir.appendingPathComponent((f as NSString).deletingPathExtension + ".png")
        try? ctx.writePNGRepresentation(of: scaled, to: out, format: .L8, colorSpace: cs)
    }
    n += 1
    if n % 100 == 0 { print(n, "/", files.count); fflush(stdout) }
}
print("done", n)
