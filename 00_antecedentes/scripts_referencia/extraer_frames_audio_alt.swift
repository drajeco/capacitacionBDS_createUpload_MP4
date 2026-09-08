import Foundation
import AVFoundation
import AppKit

let videoURL = URL(fileURLWithPath: "/Users/diegoabal/Desktop/0102/capacitacion_bancaria_balance_depositos_liquidez_audio_alt.mp4")
let outDir = URL(fileURLWithPath: "/Users/diegoabal/Desktop/0102/_work/video_frames_check_audio_alt")
try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)

let asset = AVURLAsset(url: videoURL)
let generator = AVAssetImageGenerator(asset: asset)
generator.appliesPreferredTrackTransform = true

let seconds = [1, 50, 120, 300, 600, 900, 1200, 1310]

for (idx, sec) in seconds.enumerated() {
    let time = CMTime(seconds: Double(sec), preferredTimescale: 600)
    let cgImage = try generator.copyCGImage(at: time, actualTime: nil)
    let bitmap = NSBitmapImageRep(cgImage: cgImage)
    let data = bitmap.representation(using: .png, properties: [:])!
    let url = outDir.appendingPathComponent(String(format: "frame_%02d.png", idx + 1))
    try data.write(to: url)
}

print(outDir.path)
