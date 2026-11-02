# Serenity 觀點追蹤

追 X 帳號 @aleabitoreddit（Serenity）的公開貼文，用 AI 判讀每則提到哪些股票、看多還是看空，產出一頁 `index.html`。
頁面是單一檔案，資料、樣式、程式全部內嵌，不連任何外部網站或 CDN，直接用瀏覽器打開就能看，離線也可以。

## 資料從哪來

1. **抓貼文**：在已登入 X 的 Chrome 打開 x.com/aleabitoreddit，把 `fetch_x.js` 貼到 console 執行，它會往下捲動收集貼文。
2. **送回本機**：先跑 `python3 receiver.py`，再照 `fetch_x.js` 開頭註解的指令把資料導到 http://127.0.0.1:8765/receive ，收到的貼文存成 `data/incoming.json`。
3. **合併**：`merge.py` 把 `incoming.json` 併進 `data/tweets_raw.json`（已有的貼文不覆蓋，格式壞掉的略過並回報）。
4. **AI 標籤**：`classify.py` 用 `claude` 指令列工具（訂閱帳號，不需要 API key）標出每則提到的股票與看法，存到 `data/classified.json`。已標過的不重跑。
5. **翻譯**：`translate.py` 補上繁中翻譯（貼文、她回應的內容、理由、主題）。
6. **重點摘要**：`brief.py` 產生 7 天與 28 天的重點，存到 `data/brief.json`。失敗時保留舊的。
7. **產生頁面**：`build.py` 清理資料並產出 `index.html`。

第 3 到 7 步一次跑完：`./update.sh`（任何一步失敗會停下並印出原因）。

## 架構

```
資料                          計算                    畫面
fetch_x.js  抓貼文            web/calc.js             web/template.html  頁面骨架
receiver.py 收資料              時間範圍、計數、         web/style.css      樣式
merge.py    合併                最新理由、日期標籤       web/view.js        依資料畫出列表、股票頁、貼文
classify.py AI 標籤             （純函式，可單獨測試）
translate.py 翻譯
brief.py    重點摘要
serenity/normalize.py 清理資料（別名、去重、壞資料處理、去破折號）
serenity/claude_cli.py 呼叫 claude CLI、重試、依 id 對答案
serenity/config.py    共用設定（股票別名、檔案路徑）
serenity/page.py      把上面的檔案與資料組成單一 index.html
build.py              產生 index.html 的入口
```

改樣式只要動 `web/style.css`，改文字或版面動 `web/template.html` 與 `web/view.js`，改數字怎麼算動 `web/calc.js`。改完跑 `python3 build.py` 重新產生 `index.html`。

## 怎麼跑

需要 Python 3.11 以上。AI 步驟另外需要已登入的 `claude` 指令列工具。

```
./update.sh          # 有新資料時：合併、標籤、翻譯、摘要、產生頁面
python3 build.py     # 只重新產生頁面（改了 web/ 裡的檔案之後）
open index.html      # 用瀏覽器看
```

## 怎麼測

一次跑全部：`./test.sh`（第一次要先 `npm install --no-save playwright` 並 `npx playwright install chromium`）。

1. **Python 單元測試** `python3 -m unittest discover tests`：資料清理、合併、摘要時間範圍、AI 答案對應、各步驟失敗時會大聲報錯。
2. **頁面計算單元測試** `node --test tests/calc.test.js`：今天、7 天、28 天的範圍邊界，股票計數與排序，最新理由，跳脫。
3. **頁面煙霧測試** `node tests/page.test.js`：計數與獨立 Python 驗算一致、手機與桌機不橫向捲動、惡意內容不執行、鍵盤可操作、對比度、不連外部網站、資料過期時的畫面。
4. **前後比對** `node tests/compare_pages.js 舊.html 新.html`：兩版頁面在每個畫面的文字與截圖是否完全相同（重構時用）。

GitHub Actions 在每次 push 與 PR 自動跑上面前三項，並檢查 `index.html` 是否已用最新程式重新產生。

## 已知限制

* 「Subscribe to unlock」的付費貼文只看得到開頭，頁面標成「付費貼文，只有開頭」。
* 抓貼文要手動在 Chrome 執行。全自動要靠 bb-browser 的專用瀏覽器登入 X 一次，之後可排程。
* 「7 天」「28 天」是以打開頁面的當下往回算，資料太久沒更新時這兩個分頁會是空的，重點摘要也會隱藏，請重新抓資料。
