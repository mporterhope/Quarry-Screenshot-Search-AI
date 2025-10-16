Android Ingestion Spike (Kotlin/Jetpack)

Goal
- Request Photos/Storage access; focus Screenshots folders via MediaStore
- Watch for new screenshots; import small batch
- Run ML Kit Text Recognition; persist JSON/Room

Key APIs
- MediaStore + ContentObserver
- ML Kit Text Recognition
- WorkManager (later) for background windows

Sketch (pseudo)
```kotlin
// Query MediaStore for Screenshots relative path
// Register ContentObserver for changes
// For each image: run ML Kit -> text + bounding boxes
```

Next
- Entities + type heuristics; encrypted Room
- Export compatible with backend format

