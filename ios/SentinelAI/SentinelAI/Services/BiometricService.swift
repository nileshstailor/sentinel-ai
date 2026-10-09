import LocalAuthentication
import Foundation

enum BiometricService {
    static func authenticate(reason: String) async -> Bool {
        let context = LAContext()
        var error: NSError?
        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            // Fallback to device passcode for simulator / devices without Face ID
            guard context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &error) else {
                return false
            }
            return await withCheckedContinuation { cont in
                context.evaluatePolicy(.deviceOwnerAuthentication, localizedReason: reason) { ok, _ in
                    cont.resume(returning: ok)
                }
            }
        }
        return await withCheckedContinuation { cont in
            context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: reason) { ok, _ in
                cont.resume(returning: ok)
            }
        }
    }
}
