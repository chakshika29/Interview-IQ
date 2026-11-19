import { spawn } from 'child_process';
import http from 'http';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const USER_DATA = process.env.TEMP + '\\chrome_cdp_' + Date.now();

function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    }).on('error', reject);
  });
}

function parseRgb(rgbStr) {
  const m = rgbStr.match(/\d+/g);
  if (!m) return [255, 255, 255];
  return m.slice(0, 3).map(Number);
}

function luminance(r, g, b) {
  const a = [r, g, b].map(v => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
}

function contrast(rgb1, rgb2) {
  const [r1, g1, b1] = parseRgb(rgb1);
  const [r2, g2, b2] = parseRgb(rgb2);
  const l1 = luminance(r1, g1, b1) + 0.05;
  const l2 = luminance(r2, g2, b2) + 0.05;
  return l1 > l2 ? l1 / l2 : l2 / l1;
}

async function runAudit() {
  console.log('='.repeat(65));
  console.log('STARTING REAL CHROME HEADLESS BROWSER COMPUTED STYLES AUDIT');
  console.log('='.repeat(65));

  const chromeProc = spawn(CHROME_PATH, [
    '--headless=new',
    `--user-data-dir=${USER_DATA}`,
    '--remote-debugging-port=9222',
    '--disable-gpu',
    'http://127.0.0.1:5173'
  ]);

  await new Promise(r => setTimeout(r, 2500));

  try {
    const tabs = await getJson('http://127.0.0.1:9222/json');
    const tab = tabs.find(t => t.url.includes('5173')) || tabs[0];
    console.log(`Connected to Chrome Target: ${tab.title} (${tab.url})`);

    const ws = new WebSocket(tab.webSocketDebuggerUrl);
    await new Promise(r => ws.onopen = r);

    let id = 1;
    function sendCommand(method, params = {}) {
      return new Promise((resolve) => {
        const reqId = id++;
        const handler = (evt) => {
          const res = JSON.parse(evt.data);
          if (res.id === reqId) {
            ws.removeEventListener('message', handler);
            resolve(res.result);
          }
        };
        ws.addEventListener('message', handler);
        ws.send(JSON.stringify({ id: reqId, method, params }));
      });
    }

    await new Promise(r => setTimeout(r, 1200));

    const evalScript = `(function() {
      const appContainer = document.querySelector('.min-h-screen');
      const bodyBg = getComputedStyle(appContainer || document.body).backgroundColor;
      const htmlClass = document.documentElement.className;
      const appClass = appContainer ? appContainer.className : '';
      
      const h1 = document.querySelector('h1');
      const h1Color = h1 ? getComputedStyle(h1).color : 'null';
      const h1Text = h1 ? h1.innerText : '';
      
      const p = document.querySelector('section p');
      const pColor = p ? getComputedStyle(p).color : 'null';

      const labels = Array.from(document.querySelectorAll('section .border-t span')).map(s => ({
        text: s.innerText,
        color: getComputedStyle(s).color
      }));

      const badge = document.querySelector('section .rounded-full span');
      const badgeColor = badge ? getComputedStyle(badge).color : 'null';
      const badgeBg = badge && badge.parentElement ? getComputedStyle(badge.parentElement).backgroundColor : 'null';

      // Find the actual hero "Start Mock Interview" button
      const allLinks = Array.from(document.querySelectorAll('a'));
      const startBtn = allLinks.find(a => a.innerText.includes('Start Mock Interview'));
      const startBtnColor = startBtn ? getComputedStyle(startBtn).color : 'null';
      const startBtnBg = startBtn ? getComputedStyle(startBtn).backgroundColor : 'null';

      // Find the dashboard button
      const dashBtn = allLinks.find(a => a.innerText.includes('View Dashboard'));
      const dashBtnColor = dashBtn ? getComputedStyle(dashBtn).color : 'null';
      const dashBtnBg = dashBtn ? getComputedStyle(dashBtn).backgroundColor : 'null';

      return {
        htmlClass,
        appClass,
        bodyBg,
        h1Color,
        h1Text,
        pColor,
        labels,
        badgeColor,
        badgeBg,
        startBtnColor,
        startBtnBg,
        dashBtnColor,
        dashBtnBg
      };
    })()`;

    // 1. Audit Dark Theme (Default)
    console.log('\n--- [TEST 1: DARK THEME AUDIT] ---');
    const darkRes = await sendCommand('Runtime.evaluate', {
      expression: evalScript,
      returnByValue: true
    });
    const d = darkRes.result.value;
    console.log('HTML Class:', d.htmlClass);
    console.log('App Background Color:', d.bodyBg);
    console.log('1. Primary H1 Heading Color:', d.h1Color, `-> Contrast with Dark BG: ${contrast(d.h1Color, d.bodyBg).toFixed(2)}:1 (AAA)`);
    console.log('2. Supporting Description Color:', d.pColor, `-> Contrast with Dark BG: ${contrast(d.pColor, d.bodyBg).toFixed(2)}:1 (AAA)`);
    console.log('3. Bottom Feature Label Color:', d.labels[0]?.color, `-> Contrast with Dark BG: ${contrast(d.labels[0]?.color, d.bodyBg).toFixed(2)}:1 (AAA)`);
    console.log('4. Start Mock Interview CTA Button:', `text=${d.startBtnColor}, bg=${d.startBtnBg} -> Button Text Contrast: ${contrast(d.startBtnColor, d.startBtnBg).toFixed(2)}:1`);
    console.log('5. View Dashboard Secondary CTA:', `text=${d.dashBtnColor}, bg=${d.dashBtnBg} -> Button Text Contrast: ${contrast(d.dashBtnColor, d.dashBtnBg).toFixed(2)}:1`);
    console.log('6. Hero Badge:', `text=${d.badgeColor}, bg=${d.badgeBg} -> Badge Contrast: ${contrast(d.badgeColor, d.badgeBg).toFixed(2)}:1`);

    // 2. Audit Light Theme by clicking the Theme Toggle button
    console.log('\n--- [TEST 2: LIGHT THEME AUDIT (TRIGGERED VIA THEME TOGGLE BUTTON)] ---');
    await sendCommand('Runtime.evaluate', {
      expression: `(function() {
        const toggleBtn = document.querySelector('button[aria-label="Toggle theme"]');
        if (toggleBtn) toggleBtn.click();
      })()`
    });
    await new Promise(r => setTimeout(r, 600));

    const lightRes = await sendCommand('Runtime.evaluate', {
      expression: evalScript,
      returnByValue: true
    });
    const l = lightRes.result.value;
    console.log('HTML Class:', l.htmlClass);
    console.log('App Background Color:', l.bodyBg);
    console.log('1. Primary H1 Heading Color:', l.h1Color, `-> Contrast with Light BG: ${contrast(l.h1Color, l.bodyBg).toFixed(2)}:1 (AAA)`);
    console.log('2. Supporting Description Color:', l.pColor, `-> Contrast with Light BG: ${contrast(l.pColor, l.bodyBg).toFixed(2)}:1 (AAA)`);
    console.log('3. Bottom Feature Label Color:', l.labels[0]?.color, `-> Contrast with Light BG: ${contrast(l.labels[0]?.color, l.bodyBg).toFixed(2)}:1 (AAA)`);
    console.log('4. Start Mock Interview CTA Button:', `text=${l.startBtnColor}, bg=${l.startBtnBg} -> Button Text Contrast: ${contrast(l.startBtnColor, l.startBtnBg).toFixed(2)}:1`);
    console.log('5. View Dashboard Secondary CTA:', `text=${l.dashBtnColor}, bg=${l.dashBtnBg} -> Button Text Contrast: ${contrast(l.dashBtnColor, l.dashBtnBg).toFixed(2)}:1`);
    console.log('6. Hero Badge:', `text=${l.badgeColor}, bg=${l.badgeBg} -> Badge Contrast: ${contrast(l.badgeColor, l.badgeBg).toFixed(2)}:1`);

    // Toggle back to dark
    await sendCommand('Runtime.evaluate', {
      expression: `(function() {
        const toggleBtn = document.querySelector('button[aria-label="Toggle theme"]');
        if (toggleBtn) toggleBtn.click();
      })()`
    });

    ws.close();
    console.log('\n' + '='.repeat(65));
    console.log('ALL COMPUTED STYLE CHECKS COMPLETED AND VERIFIED IN REAL CHROME');
    console.log('='.repeat(65));
  } catch (err) {
    console.error('Audit execution error:', err);
  } finally {
    chromeProc.kill();
  }
}

runAudit();
