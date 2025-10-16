iOS Ingestion Spike (Swift/SwiftUI)

Goal
- Request Photos permission (Screenshots album)
- List screenshot count; import small batch
- Run Vision OCR on-device; persist JSON/SQLite

Key APIs
- Photos: PHPhotoLibrary, PHAssetCollection (smartAlbumScreenshots)
- OCR: Vision (VNRecognizeTextRequest)
- Background: BGTaskScheduler (later)

Sketch (pseudo)
```swift
PHPhotoLibrary.requestAuthorization { _ in }
let fetch = PHAssetCollection.fetchAssetCollections(with: .smartAlbum, subtype: .smartAlbumScreenshots, options: nil)
// Iterate assets -> request image -> VNRecognizeTextRequest -> collect text + boxes
```

Next
- Background ingestion, entities, lightweight type classification
- Local encrypted DB; export compatible with backend format

