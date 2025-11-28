# S33R Security News Feed

A client-side **security news board** that aggregates content from multiple public RSS feeds.

All requests are made directly from your browser to the RSS sources via a public CORS proxy.  
No backend, no storage, no tracking.

## Features

- Live fetching of security news via RSS
- Category filters (Crypto, Malware, DFIR, Threat Intel, etc.)
- Full-text search across title, summary, source and tag
- Infinite scroll with progressive loading (feeds are fetched in parallel and rendered as they arrive)
- Dracula-inspired dark theme

## How it works

- `index.html` contains the UI and the JavaScript logic
- `styles.css` defines the Dracula theme and components
- `sec_news.opml.txt` is an OPML file listing all RSS feeds grouped by category
- The browser:
  - loads `sec_news.opml.txt`
  - maps OPML groups/subgroups to internal categories
  - fetches each RSS feed via a public CORS proxy
  - parses the XML and renders compact cards for each article

## Usage

1. Clone this repository or download the files.
2. Push them to a public GitHub repository.
3. Enable **GitHub Pages** for the repository (branch `main` / root).
4. Open the published URL – the news board will load and start fetching live feeds.

## Customization

- To use your own feeds, replace `sec_feeds.xml` with your own OPML file.
- To tweak colors or spacing, edit `styles.css` and adjust the Dracula palette or layout.
- If you want to add / remove categories:
  - Update the category buttons in `index.html`
  - Update `TYPE_LABELS` and `TYPE_MAP` in the script to match your OPML groups