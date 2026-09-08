import Foundation
import AVFoundation
import AppKit

let base = URL(fileURLWithPath: "/Users/diegoabal/Desktop/0102")
let pngDir = base.appendingPathComponent("png_finales")
let audioDir = base.appendingPathComponent("audio_por_slide_alt")
let workDir = base.appendingPathComponent("_work")
let silentURL = workDir.appendingPathComponent("video_silencioso_audio_alt.mp4")
let outputURL = base.appendingPathComponent("capacitacion_bancaria_balance_depositos_liquidez_audio_alt.mp4")

let fm = FileManager.default
try? fm.removeItem(at: silentURL)
try? fm.removeItem(at: outputURL)

let imageURLs = try fm.contentsOfDirectory(at: pngDir, includingPropertiesForKeys: nil)
    .filter { $0.pathExtension.lowercased() == "png" }
    .sorted { $0.lastPathComponent < $1.lastPathComponent }

let audioURLs = try fm.contentsOfDirectory(at: audioDir, includingPropertiesForKeys: nil)
    .filter { $0.pathExtension.lowercased() == "wav" && $0.lastPathComponent.hasPrefix("slide_") }
    .sorted { $0.lastPathComponent < $1.lastPathComponent }

guard imageURLs.count == audioURLs.count else {
    fatalError("Cantidad inconsistente: \(imageURLs.count) PNG y \(audioURLs.count) audios.")
}

let width = 960
let height = 540
let fps: Int32 = 2
let timescale: Int32 = 600

func duration(of url: URL) -> CMTime {
    let asset = AVURLAsset(url: url)
    return asset.duration
}

func pixelBuffer(from imageURL: URL, pool: CVPixelBufferPool) -> CVPixelBuffer {
    guard let nsImage = NSImage(contentsOf: imageURL) else {
        fatalError("No se pudo leer la imagen: \(imageURL.path)")
    }
    var rect = CGRect(origin: .zero, size: nsImage.size)
    guard let cgImage = nsImage.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
        fatalError("No se pudo convertir imagen: \(imageURL.path)")
    }

    var maybeBuffer: CVPixelBuffer?
    CVPixelBufferPoolCreatePixelBuffer(nil, pool, &maybeBuffer)
    guard let buffer = maybeBuffer else {
        fatalError("No se pudo crear pixel buffer.")
    }

    CVPixelBufferLockBaseAddress(buffer, [])
    defer { CVPixelBufferUnlockBaseAddress(buffer, []) }

    guard let baseAddress = CVPixelBufferGetBaseAddress(buffer) else {
        fatalError("Pixel buffer sin base address.")
    }

    let bytesPerRow = CVPixelBufferGetBytesPerRow(buffer)
    let colorSpace = CGColorSpaceCreateDeviceRGB()
    let bitmapInfo = CGBitmapInfo.byteOrder32Little.rawValue | CGImageAlphaInfo.premultipliedFirst.rawValue

    guard let context = CGContext(
        data: baseAddress,
        width: width,
        height: height,
        bitsPerComponent: 8,
        bytesPerRow: bytesPerRow,
        space: colorSpace,
        bitmapInfo: bitmapInfo
    ) else {
        fatalError("No se pudo crear CGContext.")
    }

    context.setFillColor(NSColor.white.cgColor)
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))
    context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))

    return buffer
}

let durations = audioURLs.map(duration)
let totalDuration = durations.reduce(CMTime.zero) { $0 + $1 }

let writer = try AVAssetWriter(outputURL: silentURL, fileType: .mp4)
let videoSettings: [String: Any] = [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: width,
    AVVideoHeightKey: height,
    AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: 1_200_000
    ]
]

let input = AVAssetWriterInput(mediaType: .video, outputSettings: videoSettings)
input.expectsMediaDataInRealTime = false

let attrs: [String: Any] = [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
    kCVPixelBufferWidthKey as String: width,
    kCVPixelBufferHeightKey as String: height
]

let adaptor = AVAssetWriterInputPixelBufferAdaptor(
    assetWriterInput: input,
    sourcePixelBufferAttributes: attrs
)

guard writer.canAdd(input) else {
    fatalError("No se puede agregar el track de video.")
}
writer.add(input)

guard writer.startWriting() else {
    fatalError("No se pudo iniciar escritura: \(writer.error?.localizedDescription ?? "sin detalle")")
}
writer.startSession(atSourceTime: .zero)

var cursor = CMTime.zero
let frameDuration = CMTime(value: 1, timescale: fps)
var lastImageURL: URL?

for (idx, imageURL) in imageURLs.enumerated() {
    let buffer = pixelBuffer(from: imageURL, pool: adaptor.pixelBufferPool!)
    let slideEnd = cursor + durations[idx]

    while cursor < slideEnd {
        while !input.isReadyForMoreMediaData {
            Thread.sleep(forTimeInterval: 0.02)
        }
        if !adaptor.append(buffer, withPresentationTime: cursor) {
            fatalError("No se pudo agregar frame \(idx + 1): \(writer.error?.localizedDescription ?? "sin detalle")")
        }
        cursor = cursor + frameDuration
    }
    cursor = slideEnd
    lastImageURL = imageURL
}

if let imageURL = lastImageURL {
    let buffer = pixelBuffer(from: imageURL, pool: adaptor.pixelBufferPool!)
    while !input.isReadyForMoreMediaData {
        Thread.sleep(forTimeInterval: 0.02)
    }
    _ = adaptor.append(buffer, withPresentationTime: totalDuration)
}

input.markAsFinished()
let group = DispatchGroup()
group.enter()
writer.finishWriting {
    group.leave()
}
group.wait()

if writer.status != .completed {
    fatalError("Falló video silencioso: \(writer.error?.localizedDescription ?? "sin detalle")")
}

let composition = AVMutableComposition()
guard let compVideo = composition.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid) else {
    fatalError("No se pudo crear track de video.")
}

let silentAsset = AVURLAsset(url: silentURL)
guard let silentTrack = silentAsset.tracks(withMediaType: .video).first else {
    fatalError("El video silencioso no tiene track de video.")
}
try compVideo.insertTimeRange(CMTimeRange(start: .zero, duration: totalDuration), of: silentTrack, at: .zero)

guard let compAudio = composition.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid) else {
    fatalError("No se pudo crear track de audio.")
}

cursor = .zero
for audioURL in audioURLs {
    let asset = AVURLAsset(url: audioURL)
    guard let audioTrack = asset.tracks(withMediaType: .audio).first else {
        fatalError("Audio sin track: \(audioURL.path)")
    }
    try compAudio.insertTimeRange(CMTimeRange(start: .zero, duration: asset.duration), of: audioTrack, at: cursor)
    cursor = cursor + asset.duration
}

guard let export = AVAssetExportSession(asset: composition, presetName: AVAssetExportPresetHighestQuality) else {
    fatalError("No se pudo crear exportador.")
}
export.outputURL = outputURL
export.outputFileType = .mp4
export.shouldOptimizeForNetworkUse = true

group.enter()
export.exportAsynchronously {
    group.leave()
}
group.wait()

if export.status != .completed {
    fatalError("Falló exportación final: \(export.error?.localizedDescription ?? "sin detalle")")
}

print(outputURL.path)
