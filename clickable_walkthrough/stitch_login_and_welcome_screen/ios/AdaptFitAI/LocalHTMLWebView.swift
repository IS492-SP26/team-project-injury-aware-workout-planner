import SwiftUI
import WebKit

struct LocalHTMLWebView: UIViewRepresentable {
  let url: URL

  func makeCoordinator() -> Coordinator {
    Coordinator()
  }

  func makeUIView(context: Context) -> WKWebView {
    let config = WKWebViewConfiguration()
    config.defaultWebpagePreferences.allowsContentJavaScript = true

    let view = WKWebView(frame: .zero, configuration: config)
    view.navigationDelegate = context.coordinator
    view.isOpaque = false
    view.backgroundColor = .clear
    view.scrollView.backgroundColor = .clear

    view.scrollView.isScrollEnabled = true
    view.scrollView.alwaysBounceVertical = true
    view.scrollView.showsVerticalScrollIndicator = true
    view.scrollView.showsHorizontalScrollIndicator = false
    view.scrollView.bounces = true
    view.scrollView.keyboardDismissMode = .onDrag
    view.scrollView.panGestureRecognizer.isEnabled = true
    return view
  }

  func updateUIView(_ uiView: WKWebView, context: Context) {
    guard context.coordinator.loadedURL != url else { return }
    context.coordinator.loadedURL = url

    // Re-assert scrollability in case iOS/WebKit changes it during navigation.
    uiView.scrollView.isScrollEnabled = true
    uiView.scrollView.alwaysBounceVertical = true
    uiView.scrollView.showsVerticalScrollIndicator = true
    uiView.scrollView.showsHorizontalScrollIndicator = false

    do {
      let originalHTML = try String(contentsOf: url, encoding: .utf8)
      let injectedHTML = injectiPhoneFitFix(into: originalHTML)
      uiView.loadHTMLString(injectedHTML, baseURL: url.deletingLastPathComponent())
    } catch {
      uiView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
    }
  }

  private func injectiPhoneFitFix(into html: String) -> String {
    var result = html

    if !result.contains("name=\"viewport\"") && result.contains("</head>") {
      let meta = #"<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover"/>"#
      result = result.replacingOccurrences(of: "</head>", with: "\(meta)\n</head>")
    }

    if !result.contains("id=\"ios-fit-fix\"") && result.contains("</head>") {
      let css = #"""
      <style id="ios-fit-fix">
        html, body {
          width: 100%;
          max-width: 100%;
          overflow-x: hidden;
          overflow-y: auto;
          -webkit-text-size-adjust: 100%;
          text-size-adjust: 100%;
        }
        *, *::before, *::after { box-sizing: border-box; }
        img, video, canvas, svg { max-width: 100%; height: auto; }
        table { max-width: 100%; }

        /* Preserve intended horizontal scrolling for wide tables/containers. */
        .overflow-x-auto {
          overflow-x: auto !important;
          -webkit-overflow-scrolling: touch;
        }

        /* Many exported sections use overflow-hidden on the main wrapper.
           On iPhone this can clip content, so relax it to allow scrolling. */
        .overflow-hidden {
          overflow: visible !important;
        }

        /* iPhone-sized polish: avoid desktop padding/width forcing clipping. */
        @media (max-width: 460px) {
          .max-w-7xl, .max-w-4xl, .max-w-2xl, .max-w-md, .max-w-\[850px\], .max-w-\[800px\], .max-w-\[960px\], .max-w-\[1000px\], .max-w-\[1024px\] {
            max-width: 100% !important;
          }
          .px-40, .px-20, .px-10 { padding-left: 1rem !important; padding-right: 1rem !important; }
          .p-12 { padding: 1.25rem !important; }
          .p-10 { padding: 1.25rem !important; }
          .p-8 { padding: 1.25rem !important; }
          .text-7xl { font-size: 3.5rem !important; line-height: 1 !important; }
          .text-5xl { font-size: 2.25rem !important; line-height: 1.1 !important; }
          .text-4xl { font-size: 1.875rem !important; line-height: 1.2 !important; }
        }
      </style>
      """#
      result = result.replacingOccurrences(of: "</head>", with: "\(css)\n</head>")
    }

    return result
  }

  final class Coordinator: NSObject, WKNavigationDelegate {
    var loadedURL: URL?

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
      // Some pages use full-height flex layouts; ensure the document is allowed to scroll.
      let js = #"""
      (function () {
        try {
          document.documentElement.style.overflowY = 'auto';
          document.body.style.overflowY = 'auto';
          document.documentElement.style.webkitOverflowScrolling = 'touch';
          document.body.style.webkitOverflowScrolling = 'touch';
        } catch (e) {}
      })();
      """#
      webView.evaluateJavaScript(js)

      webView.scrollView.isScrollEnabled = true
      webView.scrollView.alwaysBounceVertical = true
    }
  }
}

