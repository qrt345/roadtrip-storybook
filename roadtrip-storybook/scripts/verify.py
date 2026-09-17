"""Verify an actual generated HTML offline with an available Playwright browser."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--channel', help='Optional installed browser channel: msedge or chrome')
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright
    args.out_dir.mkdir(parents=True, exist_ok=True)
    checks = []; errors = []; network = []

    def check(name, value):
        if not value:
            raise AssertionError(name)
        checks.append(name)

    def observe(page):
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('request', lambda r: network.append(r.url) if r.url.startswith(('https:', 'http:')) else None)

    url = args.html.resolve().as_uri()
    with sync_playwright() as p:
        options = {'headless': True}
        if args.channel:
            options['channel'] = args.channel
        browser = p.chromium.launch(**options)
        version = browser.version
        desktop = browser.new_context(viewport={'width':1366,'height':768}, reduced_motion='reduce', offline=True)
        page = desktop.new_page(); observe(page); page.goto(url)
        data = json.loads(page.locator('#trip-data').text_content())
        total = len(data['pages'])
        check('dynamic page count', page.locator('#contents-list button').count() == total)
        check('first page boundary', page.get_by_role('button', name='上一页', exact=True).is_disabled())
        for i in range(total):
            page.evaluate(f'go({i})')
            check(f'page {i+1} heading', page.locator('#slide-title').is_visible())
            check(f'page {i+1} horizontal fit', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            check(f'page {i+1} desktop height', page.evaluate('document.documentElement.scrollHeight <= innerHeight+1'))
            check(f'page {i+1} map', page.locator('.board').is_visible())
            check(f'page {i+1} reduced motion', page.evaluate('!routeTimeline || !routeTimeline.isActive()'))
            for choice in page.locator('[data-choice]').all():
                choice.click()
                check(f'page {i+1} choice {choice.inner_text()}', choice.get_attribute('aria-pressed') == 'true')
            if page.locator('[data-check]').count():
                first = page.locator('[data-check]').first
                first.check(); page.reload()
                check(f'page {i+1} checklist persists', page.locator('[data-check]').first.is_checked())
                page.get_by_role('button', name='重置本页清单', exact=True).click()
                check(f'page {i+1} checklist resets', not page.locator('[data-check]').first.is_checked())
            page.screenshot(path=str(args.out_dir / f'desktop-{i+1:02}.png'), full_page=True)
        check('last page boundary', page.get_by_role('button', name='下一页', exact=True).is_disabled())
        page.keyboard.press('Home'); check('Home key', page.locator('#current-page').inner_text() == '01')
        if total > 1:
            page.keyboard.press('ArrowRight'); check('arrow key', page.locator('#current-page').inner_text() == '02')
        page.get_by_role('button', name='打开目录', exact=True).click()
        page.locator('#contents-list button').last.click()
        check('contents jump', page.locator('#current-page').inner_text() == str(total).zfill(2))
        page.get_by_role('button', name='完整资料', exact=True).click()
        check('source opens', page.locator('#source-dialog').is_visible())
        page.keyboard.press('Home')
        check('dialog blocks page shortcuts', page.locator('#current-page').inner_text() == str(total).zfill(2))
        for _ in range(12): page.keyboard.press('Tab')
        check('dialog focus', page.evaluate('!!document.activeElement.closest("#source-dialog")'))
        page.keyboard.press('Escape')
        check('Escape closes source', not page.locator('#source-dialog').is_visible())
        mobile = browser.new_context(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True, reduced_motion='reduce', offline=True)
        phone = mobile.new_page(); observe(phone); phone.goto(url)
        for i in range(total):
            phone.evaluate(f'go({i})')
            check(f'mobile {i+1} horizontal fit', phone.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            if i in (0, total-1): phone.screenshot(path=str(args.out_dir / f'mobile-{i+1:02}.png'), full_page=True)
        if total > 1:
            phone.evaluate('go(0)')
            cdp = mobile.new_cdp_session(phone)
            cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':320,'y':210}]})
            cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':85,'y':215}]})
            cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
            check('touch swipe', phone.locator('#current-page').inner_text() == '02')
        moving_context = browser.new_context(viewport={'width':1366,'height':768}, reduced_motion='no-preference', offline=True)
        moving = moving_context.new_page(); observe(moving); moving.goto(url)
        animated = next((i for i, entry in enumerate(data['pages']) if any(not leg.get('optional') for leg in (entry.get('choices') or [{}])[0].get('map', entry['map']).get('legs', []))), None)
        if animated is not None:
            moving.evaluate(f'go({animated})')
            moving.wait_for_timeout(160)
            before = moving.locator('#vehicle').get_attribute('transform'); moving.wait_for_timeout(250)
            check('vehicle moves', before != moving.locator('#vehicle').get_attribute('transform'))
            moving.get_by_role('button', name='暂停路线动画', exact=True).click()
            before = moving.locator('#vehicle').get_attribute('transform'); moving.wait_for_timeout(200)
            check('pause stops motion', before == moving.locator('#vehicle').get_attribute('transform'))
            moving.get_by_role('button', name='继续路线动画', exact=True).click(); moving.wait_for_timeout(250)
            check('resume moves', before != moving.locator('#vehicle').get_attribute('transform'))
        moving.get_by_role('button', name='关闭动效', exact=True).click()
        check('motion can be disabled', moving.evaluate('reduceMotion && (!routeTimeline || !routeTimeline.isActive())'))
        moving.reload(); check('motion preference persists', moving.get_by_role('button', name='开启动效', exact=True).is_visible())
        check('no runtime errors', not errors)
        check('offline with no external requests', not network)
        browser.close()
    result = {'html':args.html.name,'trip_id':data['id'],'pages':total,'passed':len(checks),'checks':checks,'console_errors':errors,'external_requests':network,'browser_version':version}
    (args.out_dir/'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'html':args.html.name,'pages':total,'passed':len(checks)}, ensure_ascii=True))


if __name__ == '__main__':
    main()
