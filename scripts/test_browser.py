"""Exercise the shipped panel inside the same CSP/sandbox used by Orca 1.4.185."""
import html
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orca_git_graph.app import empty_repo, render_html

CSP = "default-src 'none'; connect-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; base-uri 'none'; form-action 'none'"


def main():
    with sync_playwright() as p:
        options = {'headless': True}
        if os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE'):
            options['executable_path'] = os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']
        browser = p.chromium.launch(**options)
        page = browser.new_page(viewport={'width': 980, 'height': 680}, device_scale_factor=1)
        errors, requests = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: requests.append(request.url))
        demo = (ROOT / 'docs/demo.html').read_text(encoding='utf-8')
        def mount(document):
            source = '<meta http-equiv="Content-Security-Policy" content="' + CSP + '">' + document
            page.set_content('<body style="margin:0"><iframe title="Git Graph" sandbox="allow-scripts" style="border:0;width:100vw;height:100vh" srcdoc="' + html.escape(source, quote=True) + '"></iframe></body>')
            frame = page.frames[1]
            frame.wait_for_function('document.querySelector("#repo").disabled')
            return frame
        frame = mount(demo)
        rows = frame.locator('.row').count()
        assert rows >= 8
        assert frame.locator('#graph circle').count() == rows
        frame.locator('#search').fill('keyboard')
        assert frame.locator('.row.match').count() == 1
        frame.locator('#next').click()
        frame.locator('.row.match').click()
        assert 'keyboard' in frame.locator('#title').inner_text()
        assert 'search.js' in frame.locator('#files').inner_text()
        frame.locator('#branch').select_option('head')
        assert 0 < frame.locator('.row').count() <= rows
        frame.locator('#search').fill('')
        frame.locator('#branch').select_option('all')
        frame.locator('#head').click()
        assert frame.locator('#detail').is_visible()
        frame.locator('#close').click()
        frame.locator('#search').blur()
        page.screenshot(path=str(ROOT / 'docs/assets/git-graph.png'))
        frame = mount(render_html(empty_repo(None, 'Select a Git workspace.')))
        assert frame.locator('#empty').inner_text() == 'Select a Git workspace.'
        assert frame.locator('.row').count() == 0
        assert not errors, errors
        assert not requests, requests
        browser.close()
    print('Sandbox browser checks passed: graph, search, details, filters, HEAD, empty state, no network.')

if __name__ == '__main__':
    main()
