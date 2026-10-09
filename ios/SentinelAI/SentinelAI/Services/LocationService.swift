import CoreLocation
import Foundation

@MainActor
final class LocationService: NSObject, ObservableObject {
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined
    @Published var lastLocation: CLLocation?
    @Published var isPaused = false
    @Published var lastUploadMessage: String = "No upload yet"
    @Published var lastError: String?

    private let manager = CLLocationManager()
    private let api = APIClient.shared
    private let bridge = LocationBridge()

    override init() {
        super.init()
        manager.desiredAccuracy = kCLLocationAccuracyNearestTenMeters
        manager.distanceFilter = 25
        authorizationStatus = manager.authorizationStatus
        bridge.owner = self
        manager.delegate = bridge
    }

    func requestPermission() {
        manager.requestWhenInUseAuthorization()
    }

    func start() {
        isPaused = false
        manager.startUpdatingLocation()
    }

    func pause() {
        isPaused = true
        manager.stopUpdatingLocation()
    }

    func captureAndUpload() async {
        guard !isPaused else {
            lastUploadMessage = "Tracking paused"
            return
        }
        guard let loc = lastLocation ?? manager.location else {
            lastError = "No GPS fix yet — grant location permission and wait for a fix."
            return
        }
        do {
            let resp = try await api.uploadGPS(
                lat: loc.coordinate.latitude,
                lon: loc.coordinate.longitude,
                accuracy: loc.horizontalAccuracy,
                synthetic: false
            )
            lastUploadMessage = "Stored \(resp.event.eventId) via \(resp.mode.uppercased()) @ \(String(format: "%.5f", resp.event.lat)), \(String(format: "%.5f", resp.event.lon))"
            lastError = nil
        } catch {
            lastError = error.localizedDescription
        }
    }

    fileprivate func applyAuthorization(_ status: CLAuthorizationStatus) {
        authorizationStatus = status
        if status == .authorizedWhenInUse || status == .authorizedAlways {
            start()
        }
    }

    fileprivate func applyLocation(_ location: CLLocation) {
        lastLocation = location
    }

    fileprivate func applyError(_ message: String) {
        lastError = message
    }
}

/// Nonisolated CLLocationManagerDelegate bridge for Swift 6 concurrency.
private final class LocationBridge: NSObject, CLLocationManagerDelegate, @unchecked Sendable {
    weak var owner: LocationService?

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        let status = manager.authorizationStatus
        Task { @MainActor in
            self.owner?.applyAuthorization(status)
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let loc = locations.last else { return }
        Task { @MainActor in
            self.owner?.applyLocation(loc)
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        let message = error.localizedDescription
        Task { @MainActor in
            self.owner?.applyError(message)
        }
    }
}
