<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { processGeneratedImageToAnnotatedGrid, processImageToPerler } from './lib/perlerFromImage.js'

const mode = ref('mood')
const text = ref('')
const blockSize = ref(16)

// --- Speech Recognition (Teammate's Web Speech API) ---
const speechSupported = ref(false)
const speechListening = ref(false)
const speechError = ref('')
let speechRecognition = null

function initSpeechRecognition() {
  if (typeof window === 'undefined') return
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) return
  speechSupported.value = true
  const rec = new SR()
  rec.lang = 'zh-CN'
  rec.continuous = true
  rec.interimResults = true
  rec.maxAlternatives = 1
  rec.onresult = (event) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const res = event.results[i]
      if (!res.isFinal) continue
      const chunk = (res[0]?.transcript || '').trim()
      if (!chunk) continue
      const cur = text.value
      const sep = cur && !/\s$/.test(cur) ? ' ' : ''
      const next = (cur + sep + chunk).slice(0, 2000)
      text.value = next
    }
  }
  rec.onerror = (e) => {
    speechError.value =
      e.error === 'not-allowed'
        ? '需要麦克风权限，请在浏览器设置中允许本站使用麦克风'
        : e.error === 'no-speech'
          ? '未检测到语音，请再说一次'
          : `语音识别: ${e.error || '出错'}`
    speechListening.value = false
  }
  rec.onend = () => {
    speechListening.value = false
  }
  speechRecognition = rec
}

function toggleSpeechInput() {
  speechError.value = ''
  if (!speechRecognition) return
  if (speechListening.value) {
    try {
      speechRecognition.stop()
    } catch {
      speechListening.value = false
    }
    return
  }
  try {
    speechRecognition.start()
    speechListening.value = true
  } catch (err) {
    speechListening.value = false
    speechError.value = err instanceof Error ? err.message : '无法启动语音识别'
  }
}
// ------------------------------

const loading = ref(false)
const loadingStep = ref('')
const errorMsg = ref('')
const imageDataUrl = ref('')
const beadPalette = ref([])
const gridWidth = ref(0)
const gridHeight = ref(0)
const totalBeads = ref(0)
const resultSource = ref('')

const perlerFile = ref(null)
const gridCols = ref(56)
const colorSystem = ref('MARD')
const pixelMode = ref('dominant')
const perlerRenderStyle = ref('original')

onMounted(() => {
  initSpeechRecognition()
})

onUnmounted(() => {
  if (speechRecognition && speechListening.value) {
    try {
      speechRecognition.abort()
    } catch {
      /* ignore */
    }
  }
})

watch(mode, (newMode) => {
  errorMsg.value = ''
  imageDataUrl.value = ''
  beadPalette.value = []
  gridWidth.value = 0
  gridHeight.value = 0
  totalBeads.value = 0
  resultSource.value = ''
  
  if (newMode !== 'mood' && speechListening.value && speechRecognition) {
    try {
      speechRecognition.stop()
    } catch {
      speechListening.value = false
    }
  }
})

const colorSystemOptions = [
  { value: 'MARD', label: 'MARD' },
  { value: 'COCO', label: 'COCO' },
  { value: '漫漫', label: '漫漫' },
  { value: '盼盼', label: '盼盼' },
  { value: '咪小窝', label: '咪小窝' }
]

const apiBase = import.meta.env.VITE_API_BASE || ''

const showBrandColumn = computed(() => beadPalette.value.some((row) => row.brandKey && row.brandKey !== '—'))
const brandColumnLabel = computed(() => (resultSource.value === 'perler' ? `品牌色号（${colorSystem.value}）` : '品牌色号（MARD）'))

const canSubmit = computed(() => {
  if (loading.value) return false
  if (mode.value === 'mood') return text.value.trim().length > 0
  return perlerFile.value != null
})

function onPerlerFileChange(e) {
  const f = e.target.files?.[0]
  perlerFile.value = f || null
}

function downloadCurrentImage() {
  if (!imageDataUrl.value) return
  const link = document.createElement('a')
  link.href = imageDataUrl.value
  link.download = `generated-image-${Date.now()}.png`
  link.click()
}

async function generate() {
  errorMsg.value = ''
  imageDataUrl.value = ''
  beadPalette.value = []
  gridWidth.value = 0
  gridHeight.value = 0
  totalBeads.value = 0
  resultSource.value = ''
  loading.value = true

  try {
    if (mode.value === 'mood') {
      loadingStep.value = '正在唤醒 AI...'
      const res = await fetch(`${apiBase}/api/mood-pixel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text.value,
          blockSize: blockSize.value
        })
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        errorMsg.value = data.error || `请求失败 (${res.status})`
        return
      }
      if (data.base64Image && data.mimeType) {
        loadingStep.value = '渲染像素网格...'
        const rawImageUrl = `data:${data.mimeType};base64,${data.base64Image}`
        const annotated = await processGeneratedImageToAnnotatedGrid(rawImageUrl, {
          gridCols: Math.max(12, Math.min(48, Math.round(64 - blockSize.value))),
          maxColors: 28,
          colorSystem: 'MARD'
        })
        imageDataUrl.value = annotated.imageDataUrl
        beadPalette.value = annotated.beadPalette
        gridWidth.value = annotated.gridWidth
        gridHeight.value = annotated.gridHeight
        totalBeads.value = annotated.totalBeads
        resultSource.value = 'mood'
      } else {
        errorMsg.value = '返回数据格式异常'
      }
    } else if (mode.value === 'perler') {
      if (!perlerFile.value) {
        errorMsg.value = '请选择一张图片'
        return
      }
      let fileToProcess = perlerFile.value
      if (perlerRenderStyle.value === 'cartoon') {
        loadingStep.value = 'Agnes 卡通化处理中...'
        const fd = new FormData()
        fd.append('file', perlerFile.value)
        const res = await fetch(`${apiBase}/api/perler-cartoonize`, {
          method: 'POST',
          body: fd
        })
        const data = await res.json().catch(() => ({}))
        if (!res.ok) {
          errorMsg.value = data.error || `卡通化失败 (${res.status})`
          return
        }
        if (!data.base64Image || !data.mimeType) {
          errorMsg.value = '卡通化返回数据异常'
          return
        }
        const raw = atob(data.base64Image)
        const arr = new Uint8Array(raw.length)
        for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i)
        fileToProcess = new File([arr], 'cartoon.png', { type: data.mimeType })
      }
      loadingStep.value = '生成拼豆底稿...'
      const out = await processImageToPerler(fileToProcess, {
        gridCols: gridCols.value,
        mode: pixelMode.value,
        colorSystem: colorSystem.value,
        renderStyle: 'original'
      })
      imageDataUrl.value = out.imageDataUrl
      beadPalette.value = out.beadPalette
      gridWidth.value = out.gridWidth
      gridHeight.value = out.gridHeight
      totalBeads.value = out.totalBeads
      resultSource.value = 'perler'
    }
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '处理失败'
  } finally {
    loading.value = false
    loadingStep.value = ''
  }
}

const btnLabel = computed(() => {
  if (loading.value) return loadingStep.value || '处理中…'
  if (mode.value === 'mood') return '生成像素心情图'
  return '生成拼豆底稿'
})
</script>

<template>
  <div class="page">
    <header class="header">
      <h1>心情拼豆 / 图片拼豆</h1>
      <p class="subtitle">
        文字生成 AI 图、上传图片生成拼豆底稿。
      </p>
    </header>

    <div class="mode-tabs" role="tablist">
      <button type="button" :class="['tab', { active: mode === 'mood' }]" @click="mode = 'mood'">
        文字心情
      </button>
      <button type="button" :class="['tab', { active: mode === 'perler' }]" @click="mode = 'perler'">
        上传拼豆
      </button>
    </div>

    <main class="card">
      <template v-if="mode === 'mood'">
        <label class="field mood-text-field">
          <div class="field-label-row">
            <span>此刻的心情或想说的话</span>
            <button
              v-if="speechSupported"
              type="button"
              class="voice-btn"
              :class="{ listening: speechListening }"
              :disabled="loading"
              :title="speechListening ? '点击停止听写' : '点击开始语音输入（中文）'"
              @click="toggleSpeechInput"
            >
              {{ speechListening ? '停止听写' : '语音输入' }}
            </button>
          </div>
          <p v-if="!speechSupported" class="hint speech-hint">当前浏览器不支持语音输入，请使用 Chrome 或 Edge。</p>
          <p v-else-if="speechError" class="hint speech-error">{{ speechError }}</p>
          <textarea
            v-model="text"
            rows="4"
            maxlength="2000"
            placeholder="例如：加班结束后的轻松，又像有点空的周一傍晚……"
          />
        </label>

        <label class="field inline">
          <span>像素块大小</span>
          <input v-model.number="blockSize" type="range" min="4" max="48" step="2" />
          <span class="hint">{{ blockSize }}（越大越「马赛克」）</span>
        </label>
      </template>

      <template v-else-if="mode === 'perler'">
        <div class="section-head">
          <h2 class="section-title">照片拼豆</h2>
          <p class="section-copy">在原有拼豆生成逻辑上，支持原图直出与人像卡通化两种模式，结果图会自动带上色号和坐标轴。</p>
        </div>

        <div class="field">
          <span>功能模式</span>
          <div class="radio-group">
            <label class="radio-card">
              <input v-model="perlerRenderStyle" type="radio" value="original" />
              <span class="radio-card-main">原图直出</span>
              <span class="radio-card-sub">默认模式，保留原图色彩与明暗关系。</span>
            </label>
            <label class="radio-card">
              <input v-model="perlerRenderStyle" type="radio" value="cartoon" />
              <span class="radio-card-main">人像卡通化</span>
              <span class="radio-card-sub">后端调用 Agnes 图生图，将人像转为卡通风格后再生成拼豆底稿。</span>
            </label>
          </div>
        </div>

        <label class="field">
          <span>{{
            perlerRenderStyle === 'cartoon'
              ? '选择图片（卡通化会经后端调用 Agnes，限 JPEG/PNG）'
              : '选择图片（本地处理，不上传服务器）'
          }}</span>
          <input type="file" accept="image/*" class="file-input" @change="onPerlerFileChange" />
          <span v-if="perlerFile" class="hint file-name">{{ perlerFile.name }}</span>
        </label>

        <label class="field inline">
          <span>横向格数 N</span>
          <input v-model.number="gridCols" type="range" min="16" max="120" step="4" />
          <span class="hint">{{ gridCols }}（纵向格数按原图比例自动算）</span>
        </label>

        <label class="field">
          <span>像素化模式（与 perler-beads 一致）</span>
          <select v-model="pixelMode" class="select">
            <option value="dominant">主导色（卡通、少灰边）</option>
            <option value="average">平均色（更写实）</option>
          </select>
        </label>

        <label class="field">
          <span>品牌色号体系</span>
          <select v-model="colorSystem" class="select">
            <option v-for="o in colorSystemOptions" :key="o.value" :value="o.value">
              {{ o.label }}
            </option>
          </select>
        </label>
      </template>

      <button type="button" class="btn" :disabled="!canSubmit" @click="generate">
        {{ btnLabel }}
      </button>

      <p v-if="errorMsg" class="error">{{ errorMsg }}</p>

      <figure v-if="imageDataUrl" class="result">
        <img :src="imageDataUrl" alt="生成结果" />
        <figcaption>
          <template v-if="resultSource === 'mood'">
            逻辑网格 {{ gridWidth }}×{{ gridHeight }}，共 {{ totalBeads }} 格，已叠加颜色编码与 X/Y 坐标
          </template>
          <template v-else-if="resultSource === 'perler'">
            逻辑网格 {{ gridWidth }}×{{ gridHeight }}，共 {{ totalBeads }} 格；{{ perlerRenderStyle === 'cartoon' ? '人像卡通化' : '原图直出' }}，
            已叠加 {{ colorSystem }} 色号、HEX 与 X/Y 坐标
          </template>
        </figcaption>
      </figure>

      <div v-if="imageDataUrl" class="result-actions">
        <button type="button" class="ghost-btn" @click="downloadCurrentImage">
          下载底稿
        </button>
      </div>

      <section v-if="beadPalette.length" class="palette">
        <h2 class="palette-title">拼豆颜色用量（按颗数从多到少）</h2>
        <p class="palette-hint">
          <template v-if="resultSource === 'mood'">
            文字心情图已自动转成带颜色编码与坐标轴的拼豆底稿。后端<strong>中位切分</strong>至多 128 色。参考
            <a href="https://github.com/666ghj/MiroFish" target="_blank" rel="noopener noreferrer">MiroFish</a> 思路。
          </template>
          <template v-else>
            算法与色板数据来自
            <a href="https://github.com/Zippland/perler-beads" target="_blank" rel="noopener noreferrer">perler-beads</a>
            （AGPL-3.0）；导出图中每个色块会自动叠加品牌色号 / HEX 与完整坐标轴。
          </template>
        </p>
        <div class="palette-table-wrap">
          <table class="palette-table">
            <thead>
              <tr>
                <th>颜色</th>
                <th>HEX</th>
                <th v-if="showBrandColumn">{{ brandColumnLabel }}</th>
                <th>颗数</th>
                <th>占比</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in beadPalette" :key="idx + row.hex">
                <td class="swatch-cell">
                  <span class="swatch" :style="{ backgroundColor: row.hex }" />
                </td>
                <td class="mono">{{ row.hex }}</td>
                <td v-if="showBrandColumn" class="mono">{{ row.brandKey ?? '—' }}</td>
                <td class="num">{{ row.beadCount }}</td>
                <td class="num muted">
                  {{ totalBeads ? ((100 * row.beadCount) / totalBeads).toFixed(1) : '0' }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <footer class="footer">
      <small>
        「文字心情」与「上传拼豆 · 人像卡通化」需 Agnes 与 Java 后端；「上传拼豆 · 原图直出」在浏览器本地处理。
      </small>
    </footer>
  </div>
</template>

<style>
:root {
  --bg: #0f1115;
  --card: #1a1d24;
  --text: #e8eaef;
  --muted: #8b919c;
  --accent: #6ee7b7;
  --accent-dim: #34d399;
  --error: #f87171;
  --border: #2a2f3a;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: 'Noto Sans SC', system-ui, sans-serif;
  background: radial-gradient(ellipse 120% 80% at 50% -20%, #1e293b 0%, var(--bg) 55%);
  color: var(--text);
}

#app {
  min-height: 100vh;
}

.page {
  max-width: 720px;
  margin: 0 auto;
  padding: 2.5rem 1.25rem 3rem;
}

.header h1 {
  margin: 0 0 0.5rem;
  font-size: 1.65rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.subtitle {
  margin: 0;
  color: var(--muted);
  font-size: 0.95rem;
  line-height: 1.5;
}

.mode-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

.tab {
  flex: 1;
  min-width: 6rem;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #12151c;
  color: var(--muted);
  font: inherit;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.tab.active {
  background: rgba(52, 211, 153, 0.15);
  border-color: var(--accent-dim);
  color: var(--text);
}

.card {
  margin-top: 1rem;
  padding: 1.75rem;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
}

.section-head {
  margin-bottom: 1.25rem;
}

.section-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.section-copy {
  margin: 0.35rem 0 0;
  color: var(--muted);
  font-size: 0.85rem;
  line-height: 1.55;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.field > span:first-child {
  font-size: 0.875rem;
  color: var(--muted);
}

textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #12151c;
  color: var(--text);
  font: inherit;
  resize: vertical;
  min-height: 100px;
}

textarea:focus {
  outline: none;
  border-color: var(--accent-dim);
  box-shadow: 0 0 0 2px rgba(52, 211, 153, 0.2);
}

.file-input {
  padding: 0.5rem 0;
  font: inherit;
  color: var(--muted);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.file-name {
  color: var(--accent-dim);
}

.select {
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #12151c;
  color: var(--text);
  font: inherit;
}

.field.inline {
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.field.inline input[type='range'] {
  flex: 1;
  min-width: 120px;
  accent-color: var(--accent-dim);
}

.hint {
  font-size: 0.8rem;
  color: var(--muted);
  width: 100%;
  margin-left: 0;
}

.radio-group {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.radio-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding: 0.9rem 1rem 0.9rem 2.8rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #12151c;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, transform 0.15s;
}

.radio-card:hover {
  border-color: rgba(52, 211, 153, 0.45);
}

.radio-card input {
  position: absolute;
  top: 1rem;
  left: 1rem;
  width: 1rem;
  height: 1rem;
  margin: 0;
  accent-color: var(--accent-dim);
}

.radio-card:has(input:checked) {
  border-color: var(--accent-dim);
  background: rgba(52, 211, 153, 0.1);
  transform: translateY(-1px);
}

.radio-card-main {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text);
}

.radio-card-sub {
  color: var(--muted);
  font-size: 0.8rem;
  line-height: 1.45;
}

.ghost-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 8rem;
  padding: 0.72rem 1rem;
  border: 1px solid rgba(110, 231, 183, 0.35);
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.35);
  color: var(--text);
  font: inherit;
  font-size: 0.9rem;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.ghost-btn:hover {
  border-color: var(--accent-dim);
  background: rgba(52, 211, 153, 0.1);
}

.btn {
  width: 100%;
  padding: 0.85rem 1.25rem;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #34d399, #10b981);
  color: #0f172a;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
}

.btn:hover:not(:disabled) {
  opacity: 0.95;
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.error {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
  background: rgba(248, 113, 113, 0.12);
  color: var(--error);
  font-size: 0.9rem;
}

.result {
  margin: 1.5rem 0 0;
  padding: 0;
}

.result img {
  display: block;
  width: 100%;
  max-width: 512px;
  margin: 0 auto;
  border-radius: 8px;
  border: 1px solid var(--border);
  image-rendering: pixelated;
  image-rendering: crisp-edges;
}

.result figcaption {
  margin-top: 0.75rem;
  text-align: center;
  font-size: 0.8rem;
  color: var(--muted);
}

.palette {
  margin-top: 1.75rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border);
}

.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.palette-title {
  margin: 0 0 0.5rem;
  font-size: 1.05rem;
  font-weight: 600;
}

.palette-hint {
  margin: 0 0 1rem;
  font-size: 0.8rem;
  color: var(--muted);
  line-height: 1.5;
}

.palette-hint a {
  color: var(--accent-dim);
}

.palette-table-wrap {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid var(--border);
}

.palette-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.palette-table th,
.palette-table td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.palette-table th {
  background: #12151c;
  color: var(--muted);
  font-weight: 600;
}

.palette-table tbody tr:last-child td {
  border-bottom: none;
}

.swatch-cell {
  width: 3rem;
}

.swatch {
  display: inline-block;
  width: 2rem;
  height: 2rem;
  border-radius: 4px;
  border: 1px solid var(--border);
  vertical-align: middle;
}

.mono {
  font-family: ui-monospace, monospace;
}

.num {
  font-variant-numeric: tabular-nums;
}

.muted {
  color: var(--muted);
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-voice {
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--accent);
  border-radius: 4px;
  padding: 0.2rem 0.5rem;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-voice:hover:not(:disabled) {
  background: rgba(110, 231, 183, 0.1);
}

.btn-voice.recording {
  border-color: var(--error);
  color: var(--error);
  animation: pulse 1.5s infinite;
}

.btn-voice:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: var(--muted);
  color: var(--muted);
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(248, 113, 113, 0.4); }
  70% { box-shadow: 0 0 0 4px rgba(248, 113, 113, 0); }
  100% { box-shadow: 0 0 0 0 rgba(248, 113, 113, 0); }
}

.footer {
  margin-top: 2rem;
  text-align: center;
}

.footer small {
  color: var(--muted);
  font-size: 0.75rem;
}

@media (max-width: 640px) {
  .card {
    padding: 1.15rem;
  }

  .radio-group {
    grid-template-columns: 1fr;
  }

  .radio-card {
    padding-left: 2.6rem;
  }

  .result-actions {
    flex-direction: column;
  }

  .ghost-btn {
    width: 100%;
  }
}
</style>
