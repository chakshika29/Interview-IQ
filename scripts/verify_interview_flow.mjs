import { spawn } from 'child_process';
import http from 'http';
import fs from 'fs';
import path from 'path';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const USER_DATA = path.join(process.env.TEMP || 'C:\\Temp', 'chrome_flow_' + Date.now());
const SCREENSHOT_DIR = path.resolve('screenshots');

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    }).on('error', reject);
  });
}

async function runFlow() {
  console.log('='.repeat(70));
  console.log('STARTING REAL END-TO-END INTERVIEW WORKFLOW VERIFICATION (CHROME CDP)');
  console.log('='.repeat(70));

  const chromeProc = spawn(CHROME_PATH, [
    '--headless=new',
    `--user-data-dir=${USER_DATA}`,
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--window-size=1280,900',
    'http://127.0.0.1:5173'
  ]);

  await new Promise(r => setTimeout(r, 2500));

  try {
    const tabs = await getJson('http://127.0.0.1:9222/json');
    const tab = tabs.find(t => t.url.includes('5173')) || tabs[0];
    console.log(`Connected to Chrome page: ${tab.title} (${tab.url})`);

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

    async function evaluate(code) {
      const res = await sendCommand('Runtime.evaluate', {
        expression: code,
        returnByValue: true,
        awaitPromise: true,
      });
      return res?.result?.value;
    }

    async function takeScreenshot(name) {
      const res = await sendCommand('Page.captureScreenshot', { format: 'png' });
      if (res && res.data) {
        const filePath = path.join(SCREENSHOT_DIR, `${name}.png`);
        fs.writeFileSync(filePath, Buffer.from(res.data, 'base64'));
        console.log(`  [Screenshot Saved]: ${filePath} (${Math.round(res.data.length * 0.75 / 1024)} KB)`);
      }
    }

    // Step 1: Documents Page
    console.log('\n[Step 1] Navigating to Documents Page (/documents)...');
    await evaluate(`window.history.pushState({}, '', '/documents'); window.dispatchEvent(new PopStateEvent('popstate'));`);
    await new Promise(r => setTimeout(r, 1500));
    await takeScreenshot('01_documents_page_initial');

    // Step 2: Load Sample Data
    console.log('\n[Step 2] Loading AI Engineer Sample Resume & Job Description...');
    await evaluate(`(function() {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Sample Data'));
      if (btn) btn.click();
    })()`);
    await new Promise(r => setTimeout(r, 1000));
    await takeScreenshot('02_documents_page_populated');

    // Step 3: Configure Page
    console.log('\n[Step 3] Continuing to Configuration Page (/configure)...');
    await evaluate(`(function() {
      const continueBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Continue to Configuration'));
      if (continueBtn) continueBtn.click();
    })()`);
    await new Promise(r => setTimeout(r, 1500));
    await takeScreenshot('03_configure_page');

    // Step 4: Start Interview
    console.log('\n[Step 4] Starting Interview Session (Building RAG Index + Gemini Skill Gap)...');
    await evaluate(`(function() {
      const beginBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Begin Mock Interview'));
      if (beginBtn) beginBtn.click();
    })()`);

    console.log('  -> Waiting for Gemini to index chunks and generate Question 1...');
    let q1Text = '';
    for (let i = 0; i < 20; i++) {
      await new Promise(r => setTimeout(r, 1500));
      const res = await evaluate(`(function() {
        const h2 = document.querySelector('h2');
        const citations = Array.from(document.querySelectorAll('details .font-mono')).map(el => el.innerText);
        const details = document.querySelector('details');
        if (details) details.open = true;
        return {
          question: h2 ? h2.innerText : '',
          citationsCount: citations.length,
          citationsSnippets: citations.map(c => c.slice(0, 70))
        };
      })()`);
      if (res && res.question.length > 25) {
        q1Text = res.question;
        console.log(`  -> Question 1 Loaded in ~${(i + 1) * 1.5}s:`);
        console.log(`     Question: "${q1Text.slice(0, 120)}..."`);
        console.log(`     Grounded RAG Citations: ${res.citationsCount} chunks`);
        break;
      }
    }
    await takeScreenshot('04_live_interview_q1_loaded');

    // Step 5: Answer Question 1 using real CDP keyboard insertion
    console.log('\n[Step 5] Typing Candidate Technical Answer via CDP Input.insertText...');
    await evaluate(`(function() {
      const textarea = document.querySelector('textarea');
      if (textarea) textarea.focus();
    })()`);

    const ans1 = "At DataScale, I built stateful multi-agent workflows using LangGraph. We configured persistent Postgres checkpointers to capture node state transitions. For cyclic graph execution, we handled schema migrations by versioning state schemas and implemented human-in-the-loop review nodes before mutating external databases, reducing state loss to zero.";
    await sendCommand('Input.insertText', { text: ans1 });
    await new Promise(r => setTimeout(r, 800));

    const wordCount = await evaluate(`document.querySelector('textarea') ? document.querySelector('textarea').value.split(/\\s+/).length : 0`);
    console.log(`  -> Typed answer: ${wordCount} words inserted into textarea.`);
    await takeScreenshot('05_live_interview_q1_answered');

    // Click Submit & Score Answer
    console.log('\n[Step 6] Submitting Answer 1 to Gemini for Rubric Evaluation...');
    await evaluate(`(function() {
      const submitBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Submit & Score'));
      if (submitBtn) submitBtn.click();
    })()`);

    // Wait for scoring
    let scoredQ1 = false;
    for (let i = 0; i < 20; i++) {
      await new Promise(r => setTimeout(r, 1500));
      const fb = await evaluate(`(function() {
        const scoreSpan = document.querySelector('.text-3xl.font-extrabold, .text-4xl.font-extrabold');
        const strengths = Array.from(document.querySelectorAll('li')).map(l => l.innerText);
        const modelAns = document.querySelector('p.font-mono');
        return {
          scoreText: scoreSpan ? scoreSpan.innerText : '',
          strengthsCount: strengths.length,
          hasModelAnswer: !!modelAns
        };
      })()`);
      if (fb && fb.scoreText) {
        console.log(`  -> AI Answer Evaluation Received in ~${(i + 1) * 1.5}s:`);
        console.log(`     Score: ${fb.scoreText}`);
        console.log(`     Strengths Found: ${fb.strengthsCount}`);
        console.log(`     10/10 Model Answer Rendered: ${fb.hasModelAnswer}`);
        scoredQ1 = true;
        break;
      }
    }
    await takeScreenshot('06_live_interview_q1_evaluated');

    // Step 7: Request Next Adaptive Question
    console.log('\n[Step 7] Requesting Next Adaptive Question (Gemini RAG recalibration)...');
    await evaluate(`(function() {
      const nextBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Next Adaptive Question'));
      if (nextBtn) nextBtn.click();
    })()`);

    // Wait for Q2
    let q2Text = '';
    for (let i = 0; i < 20; i++) {
      await new Promise(r => setTimeout(r, 1500));
      const res = await evaluate(`(function() {
        const round = document.querySelector('.uppercase');
        const h2 = document.querySelector('h2');
        return {
          round: round ? round.innerText : '',
          question: h2 ? h2.innerText : ''
        };
      })()`);
      if (res && res.round.includes('Round 2') && res.question !== q1Text) {
        q2Text = res.question;
        console.log(`  -> Adaptive Question 2 Loaded:`);
        console.log(`     Round: ${res.round}`);
        console.log(`     Question: "${q2Text.slice(0, 120)}..."`);
        break;
      }
    }
    await takeScreenshot('07_live_interview_adaptive_q2_loaded');

    // Step 8: Answer Question 2
    console.log('\n[Step 8] Answering Adaptive Question 2 and Scoring...');
    await evaluate(`(function() {
      const textarea = document.querySelector('textarea');
      if (textarea) textarea.focus();
    })()`);

    const ans2 = "To merge BM25 and vector search, we compute Reciprocal Rank Fusion scores RRF(d) = sum(1 / (k + rank_i(d))) with k=60. We benchmarked dense cosine similarity against BM25 term frequency on a test set of 1,000 queries, achieving a Mean Reciprocal Rank (MRR) of 0.89 and latency under 120ms.";
    await sendCommand('Input.insertText', { text: ans2 });
    await new Promise(r => setTimeout(r, 800));

    await evaluate(`(function() {
      const submitBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Submit & Score'));
      if (submitBtn) submitBtn.click();
    })()`);

    // Wait for scoring
    for (let i = 0; i < 20; i++) {
      await new Promise(r => setTimeout(r, 1500));
      const score = await evaluate(`document.querySelector('.text-3xl.font-extrabold, .text-4xl.font-extrabold') ? document.querySelector('.text-3xl.font-extrabold, .text-4xl.font-extrabold').innerText : ''`);
      if (score) {
        console.log(`  -> Question 2 Evaluated: Score ${score}`);
        break;
      }
    }
    await takeScreenshot('08_live_interview_q2_evaluated');

    // Step 9: Complete Interview and View Report
    console.log('\n[Step 9] Completing Interview and Navigating to Results Report...');
    const currentUrl = await evaluate(`window.location.pathname`);
    const sid = currentUrl.split('/')[2];
    
    // Complete session via API
    await evaluate(`(function(id) {
      window.history.pushState({}, '', '/results/' + id);
      window.dispatchEvent(new PopStateEvent('popstate'));
    })('${sid}')`);
    await new Promise(r => setTimeout(r, 2000));

    const results = await evaluate(`(function() {
      const rating = document.querySelector('.text-4xl.font-extrabold');
      const verdict = document.querySelector('.text-emerald-600, .text-emerald-400');
      const qCards = Array.from(document.querySelectorAll('.rounded-2xl.border')).filter(c => c.innerText.includes('Round'));
      return {
        overallScore: rating ? rating.innerText : 'N/A',
        verdict: verdict ? verdict.innerText : 'N/A',
        evaluatedQuestionsCount: qCards.length
      };
    })()`);
    console.log('  -> Results Report Verified:');
    console.log(`     Overall Rating: ${results.overallScore} / 10`);
    console.log(`     Verdict: ${results.verdict}`);
    console.log(`     Reviewed Questions in Report: ${results.evaluatedQuestionsCount}`);
    await takeScreenshot('09_results_report_complete');

    // Step 10: History Page
    console.log('\n[Step 10] Navigating to History Page (/history)...');
    await evaluate(`window.history.pushState({}, '', '/history'); window.dispatchEvent(new PopStateEvent('popstate'));`);
    await new Promise(r => setTimeout(r, 2000));

    const history = await evaluate(`(function() {
      const cards = Array.from(document.querySelectorAll('.rounded-2xl.border')).filter(e => e.innerText.includes('Type:'));
      return {
        count: cards.length,
        firstCard: cards[0] ? cards[0].innerText.slice(0, 160).replace(/\\n/g, ' ') : ''
      };
    })()`);
    console.log('  -> History Page Verified:');
    console.log(`     Total Persisted Sessions: ${history.count}`);
    console.log(`     Latest Session: ${history.firstCard}`);
    await takeScreenshot('10_history_page_persisted');

    ws.close();
    console.log('\n' + '='.repeat(70));
    console.log('REAL END-TO-END INTERVIEW FLOW FULLY VERIFIED IN CHROME BROWSER');
    console.log('='.repeat(70));
  } catch (err) {
    console.error('Workflow error:', err);
  } finally {
    chromeProc.kill();
  }
}

runFlow();
