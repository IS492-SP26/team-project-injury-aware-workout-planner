import SwiftUI

struct ScreenWebView: View {
  let screen: Screen

  var body: some View {
    let url =
      Bundle.main.url(forResource: screen.resourceName, withExtension: "html")
      ?? Bundle.main.url(forResource: screen.resourceName, withExtension: "html", subdirectory: "Resources")

    if let url {
      LocalHTMLWebView(url: url)
    } else {
      let visibleHTML =
        (Bundle.main.urls(forResourcesWithExtension: "html", subdirectory: nil) ?? [])
        + (Bundle.main.urls(forResourcesWithExtension: "html", subdirectory: "Resources") ?? [])

        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle")
                .font(.largeTitle)

            Text("Missing resource")
                .font(.headline)

            Text(
                """
                Could not find `\(screen.resourceName).html` in the app bundle.

                Found HTML files:
                \(visibleHTML.map(\.lastPathComponent).sorted().joined(separator: "\n"))
                """
            )
            .font(.subheadline)
            .multilineTextAlignment(.center)
        }
        .padding()
    }
  }
}

