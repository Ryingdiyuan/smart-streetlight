<template>
  <section class="map-page">
    <header class="map-header">
      <div class="map-header-left">
        <p class="section-kicker">GIS Visualization</p>
        <h2>设备地图</h2>
      </div>
      <div class="map-header-right">
        <div class="map-legend">
          <span class="legend-item"><span class="legend-dot online"></span>在线</span>
          <span class="legend-item"><span class="legend-dot offline"></span>离线</span>
          <span class="legend-item"><span class="legend-dot lamp-on"></span>灯亮</span>
          <span class="legend-item"><span class="legend-dot lamp-off"></span>灯灭</span>
        </div>
        <span class="device-count">共 {{ devices.length }} 台设备</span>
        <button class="ghost-button" type="button" @click="refreshDevices" :disabled="loading">
          {{ loading ? '刷新中…' : '刷新' }}
        </button>
      </div>
    </header>

    <div class="map-container-wrapper">
      <div ref="mapContainer" class="map-container"></div>

      <!-- 提示：点击地图添加设备 / 拖动标记修改坐标 -->
      <div class="map-hint">点击地图空白处添加设备 · 拖动标记可修改坐标</div>

      <!-- 加载状态 -->
      <div v-if="loading && devices.length === 0" class="map-loading">
        <div class="loading-spinner"></div>
        <p>加载地图数据…</p>
      </div>

      <!-- 无坐标提示 -->
      <div v-if="!loading && devices.length > 0 && noCoordDevices.length > 0" class="map-tip">
        ⚠️ {{ noCoordDevices.length }} 台设备缺少 GPS 坐标，未在地图上显示
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="map-error">
        <p>❌ {{ error }}</p>
        <button class="ghost-button" @click="refreshDevices">重试</button>
      </div>
    </div>

    <!-- ====== 添加设备弹窗 ====== -->
    <Teleport to="body">
      <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
        <div class="modal-card card">
          <div class="modal-header">
            <h3>添加设备</h3>
            <button class="ghost-button" type="button" @click="closeAddModal">✕</button>
          </div>

          <form class="modal-body" @submit.prevent="handleAddDevice">
            <div class="form-row">
              <label>
                <span>设备编号 <em>*</em></span>
                <input
                  v-model="form.deviceCode"
                  class="search-input"
                  type="text"
                  placeholder="例如 SL-004"
                  required
                  maxlength="64"
                />
              </label>
            </div>

            <div class="form-row">
              <label>
                <span>设备名称 <em>*</em></span>
                <input
                  v-model="form.deviceName"
                  class="search-input"
                  type="text"
                  placeholder="例如 四号路灯"
                  required
                  maxlength="100"
                />
              </label>
            </div>

            <div class="form-row">
              <label>
                <span>位置描述</span>
                <input
                  v-model="form.location"
                  class="search-input"
                  type="text"
                  placeholder="例如 操场东侧"
                  maxlength="255"
                />
              </label>
            </div>

            <div class="form-row form-row-coords">
              <label>
                <span>纬度</span>
                <input
                  :value="form.latitude.toFixed(6)"
                  class="search-input"
                  type="text"
                  disabled
                />
              </label>
              <label>
                <span>经度</span>
                <input
                  :value="form.longitude.toFixed(6)"
                  class="search-input"
                  type="text"
                  disabled
                />
              </label>
            </div>

            <p v-if="addError" class="form-error">{{ addError }}</p>

            <div class="modal-actions">
              <button class="ghost-button" type="button" @click="closeAddModal">取消</button>
              <button class="primary-button" type="submit" :disabled="submitting">
                {{ submitting ? '添加中…' : '确认添加' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- ====== 坐标更新确认弹窗 ====== -->
    <Teleport to="body">
      <div v-if="showCoordConfirm" class="modal-overlay" @click.self="cancelCoordUpdate">
        <div class="modal-card card">
          <div class="modal-header">
            <h3>更新设备坐标</h3>
            <button class="ghost-button" type="button" @click="cancelCoordUpdate">✕</button>
          </div>

          <div class="modal-body">
            <p>是否将 <strong>{{ draggingDevice?.deviceName }}</strong> 的坐标更新为：</p>

            <div class="coord-preview">
              <span class="coord-label">纬度</span>
              <code>{{ newLatitude.toFixed(6) }}</code>
              <span class="coord-label">经度</span>
              <code>{{ newLongitude.toFixed(6) }}</code>
            </div>

            <p v-if="coordUpdateError" class="form-error">{{ coordUpdateError }}</p>

            <div class="modal-actions">
              <button class="ghost-button" type="button" @click="cancelCoordUpdate">取消</button>
              <button class="primary-button" type="button" :disabled="coordUpdating" @click="confirmCoordUpdate">
                {{ coordUpdating ? '保存中…' : '保存坐标' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from "vue";

import { createDevice, getDeviceList, updateDevice } from "@/services/api/deviceService";
import type { Device } from "@/types/models";

// ---- 组件状态 ----
const mapContainer = ref<HTMLDivElement | null>(null);
const devices = ref<Device[]>([]);
const noCoordDevices = ref<Device[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

let map: AMapMap | null = null;
let markers: AMapMarker[] = [];
let infoWindow: AMapInfoWindow | null = null;
let refreshTimer: ReturnType<typeof setInterval> | null = null;

const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || "";

// ---- 添加设备弹窗状态 ----
const showAddModal = ref(false);
const submitting = ref(false);
const addError = ref<string | null>(null);

const form = reactive({
  deviceCode: "",
  deviceName: "",
  location: "",
  latitude: 0,
  longitude: 0,
});

// ---- 拖拽更新坐标状态 ----
const draggingDevice = ref<Device | null>(null);
const showCoordConfirm = ref(false);
const newLatitude = ref(0);
const newLongitude = ref(0);
const coordUpdateError = ref<string | null>(null);
const coordUpdating = ref(false);

function cancelCoordUpdate() {
  showCoordConfirm.value = false;
  draggingDevice.value = null;
  coordUpdateError.value = null;
}

async function confirmCoordUpdate() {
  if (!draggingDevice.value) return;
  coordUpdating.value = true;
  coordUpdateError.value = null;
  try {
    await updateDevice(draggingDevice.value.id, {
      latitude: newLatitude.value,
      longitude: newLongitude.value,
    });
    showCoordConfirm.value = false;
    draggingDevice.value = null;
    await refreshDevices();
  } catch (e) {
    coordUpdateError.value = e instanceof Error ? e.message : "更新坐标失败";
  } finally {
    coordUpdating.value = false;
  }
}

function closeAddModal() {
  showAddModal.value = false;
  addError.value = null;
  form.deviceCode = "";
  form.deviceName = "";
  form.location = "";
}

async function handleAddDevice() {
  if (!form.deviceCode || !form.deviceName) return;
  submitting.value = true;
  addError.value = null;
  try {
    await createDevice({
      device_code: form.deviceCode,
      device_name: form.deviceName,
      location: form.location || undefined,
      latitude: form.latitude,
      longitude: form.longitude,
    });
    closeAddModal();
    await refreshDevices();
  } catch (e) {
    addError.value = e instanceof Error ? e.message : "添加设备失败";
  } finally {
    submitting.value = false;
  }
}

// ---- 地图点击处理 ----
function onMapClick(e: { lnglat: AMapLngLat }) {
  form.latitude = e.lnglat.lat;
  form.longitude = e.lnglat.lng;
  form.deviceCode = "";
  form.deviceName = "";
  form.location = "";
  showAddModal.value = true;
}

// ---- 工具函数 ----
function getMarkerColor(device: Device): string {
  if (device.status === "online") {
    return device.lampStatus === "ON" ? "#fbbf24" : "#22c55e";
  }
  return "#ef4444";
}

function buildInfoContent(device: Device): string {
  const statusLabel = device.status === "online" ? "在线" : "离线";
  const lampLabel = device.lampStatus === "ON" ? "亮" : "灭";
  return `
    <div class="amap-info-window">
      <h3>${device.deviceName}</h3>
      <table>
        <tr><td>设备编号</td><td>${device.deviceCode}</td></tr>
        <tr><td>位置</td><td>${device.location}</td></tr>
        <tr><td>坐标</td><td>${device.latitude?.toFixed(4)}, ${device.longitude?.toFixed(4)}</td></tr>
        <tr><td>状态</td><td>${statusLabel}</td></tr>
        <tr><td>灯具</td><td>${lampLabel}</td></tr>
        <tr><td>最后心跳</td><td>${device.lastHeartbeatAt}</td></tr>
      </table>
      <a href="/devices/${device.id}" class="amap-info-link">查看详情 →</a>
    </div>
  `;
}

function createMarkerElement(device: Device): HTMLDivElement {
  const el = document.createElement("div");
  el.className = "custom-marker";
  const color = getMarkerColor(device);
  const pulseColor = device.status === "online" ? "#22c55e" : "#ef4444";
  el.innerHTML = `
    <div class="marker-pulse" style="background:${pulseColor}40;border-color:${pulseColor}"></div>
    <div class="marker-icon" style="background:${color}">
      <svg viewBox="0 0 24 24" fill="white" width="16" height="16">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
      </svg>
    </div>
  `;
  return el;
}

// ---- 加载高德地图 ----
async function loadAmap(): Promise<void> {
  if (window.AMap) return;

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}`;
    script.async = true;
    script.onload = () => {
      window.AMap.plugin(["AMap.MoveAnimation"], () => {
        resolve();
      });
    };
    script.onerror = () => reject(new Error("高德地图 API 加载失败"));
    document.head.appendChild(script);
  });
}

// ---- 初始化地图 ----
async function initMap(): Promise<void> {
  if (!mapContainer.value) return;
  if (!AMAP_KEY) {
    error.value = "请先在 frontend/.env 中配置 VITE_AMAP_KEY";
    return;
  }

  try {
    await loadAmap();
  } catch {
    error.value = "高德地图 API 加载失败，请检查网络或 API Key";
    return;
  }

  map = new window.AMap.Map(mapContainer.value, {
    zoom: 16,
    center: [106.528, 29.531],
    mapStyle: "amap://styles/light",
    resizeEnable: true,
  });

  infoWindow = new window.AMap.InfoWindow({ offset: [0, -30] });

  // 点击地图空白处 → 打开添加设备弹窗
  map.on("click", onMapClick);

  await refreshDevices();
}

// ---- 清除标记 ----
function clearMarkers(): void {
  markers.forEach((m) => m.setMap(null));
  markers = [];
}

// ---- 刷新设备 + 更新标记 ----
async function refreshDevices(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    const allDevices = await getDeviceList();
    devices.value = allDevices;

    const coordDevices = allDevices.filter(
      (d) => d.latitude !== undefined && d.longitude !== undefined,
    );
    noCoordDevices.value = allDevices.filter(
      (d) => d.latitude === undefined || d.longitude === undefined,
    );

    if (map) {
      clearMarkers();
      markers = coordDevices.map((device) => {
        const marker = new window.AMap.Marker({
          position: [device.longitude!, device.latitude!],
          content: createMarkerElement(device),
          offset: new window.AMap.Pixel(-12, -24),
          draggable: true,
        });
        marker.setMap(map!);

        marker.on("dragstart", () => {
          // 标记拖拽开始，清除之前可能残留的状态
          (marker as any)._dragHandled = false;
        });

        marker.on("dragend", () => {
          // 标记拖拽结束 → 弹出坐标确认弹窗
          (marker as any)._dragHandled = true;
          const pos = marker.getPosition();
          draggingDevice.value = device;
          newLatitude.value = pos.lat;
          newLongitude.value = pos.lng;
          showCoordConfirm.value = true;
        });

        marker.on("click", (e) => {
          // 阻止事件冒泡，避免触发地图 click → 打开添加设备弹窗
          if (typeof e.stopPropagation === "function") {
            e.stopPropagation();
          }

          // 如果 dragend 已经处理过这次操作，跳过
          if ((marker as any)._dragHandled) {
            (marker as any)._dragHandled = false;
            return;
          }

          // 检测标记位置是否已变化（小幅拖拽可能只触发了 click 未触发 dragend）
          const pos = marker.getPosition();
          const origLat = device.latitude ?? 0;
          const origLng = device.longitude ?? 0;
          if (
            Math.abs(pos.lat - origLat) > 0.000001 ||
            Math.abs(pos.lng - origLng) > 0.000001
          ) {
            // 标记被移动了 → 弹出坐标确认弹窗
            draggingDevice.value = device;
            newLatitude.value = pos.lat;
            newLongitude.value = pos.lng;
            showCoordConfirm.value = true;
            return;
          }

          // 正常点击 → 打开信息窗口
          infoWindow?.setContent(buildInfoContent(device));
          infoWindow?.open(map!, marker.getPosition());
        });

        return marker;
      });

      if (markers.length > 0) {
        map.setFitView(markers, false, [50, 50, 50, 50]);
      }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : "获取设备数据失败";
  } finally {
    loading.value = false;
  }
}

// ---- 生命周期 ----
onMounted(() => {
  initMap();
  refreshTimer = setInterval(refreshDevices, 30000);
});

onUnmounted(() => {
  if (map) {
    map.off("click", onMapClick);
  }
  clearMarkers();
  if (infoWindow) {
    infoWindow.close();
  }
  if (map) {
    map.destroy();
    map = null;
  }
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
});
</script>

<style scoped>
.map-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* ---- 头部 ---- */
.map-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.map-header-left {
  flex-shrink: 0;
}

.map-header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.map-legend {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: var(--text-secondary, #64748b);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.online { background: #22c55e; }
.legend-dot.offline { background: #ef4444; }
.legend-dot.lamp-on { background: #fbbf24; }
.legend-dot.lamp-off { background: #94a3b8; }

.device-count {
  font-size: 0.85rem;
  color: var(--text-secondary, #64748b);
  background: var(--bg-muted, #f1f5f9);
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
}

/* ---- 地图容器 ---- */
.map-container-wrapper {
  position: relative;
  flex: 1;
  min-height: 400px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-color, #e2e8f0);
}

.map-container {
  width: 100%;
  height: 100%;
}

.map-hint {
  position: absolute;
  top: 0.75rem;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-primary, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  padding: 0.35rem 1rem;
  border-radius: 999px;
  font-size: 0.8rem;
  color: var(--text-secondary, #64748b);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  z-index: 10;
  pointer-events: none;
  white-space: nowrap;
}

/* ---- 覆盖层 ---- */
.map-loading,
.map-error {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: var(--bg-primary, #ffffff);
  z-index: 10;
}

.map-tip {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-primary, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary, #64748b);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  z-index: 10;
  white-space: nowrap;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color, #e2e8f0);
  border-top-color: var(--accent, #3b82f6);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ---- 弹窗 ---- */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  width: 420px;
  max-width: 90vw;
  padding: 1.5rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.85rem;
  color: var(--text-secondary, #64748b);
}

.form-row label em {
  color: #ef4444;
  font-style: normal;
}

.form-row-coords {
  display: flex;
  gap: 1rem;
}

.form-row-coords label {
  flex: 1;
}

.form-error {
  color: #ef4444;
  font-size: 0.85rem;
  margin: 0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

/* ---- 坐标更新预览 ---- */
.coord-preview {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-muted, #f1f5f9);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.85rem;
}

.coord-label {
  color: var(--text-secondary, #64748b);
  white-space: nowrap;
}

.coord-preview code {
  font-family: "SF Mono", "Fira Code", monospace;
  color: var(--accent, #3b82f6);
  font-weight: 600;
}
</style>

<style>
/* ---- 全局：自定义标记样式 ---- */
.custom-marker {
  position: relative;
  cursor: pointer;
}

.marker-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  border: 2px solid;
  animation: pulse 2s ease-out infinite;
  pointer-events: none;
}

@keyframes pulse {
  0% {
    transform: translate(-50%, -50%) scale(0.5);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.8);
    opacity: 0;
  }
}

.marker-icon {
  width: 28px;
  height: 28px;
  border-radius: 50% 50% 50% 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transform: rotate(-45deg);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.marker-icon svg {
  transform: rotate(45deg);
}

/* ---- 信息窗口 ---- */
.amap-info-window {
  padding: 0.5rem 0.25rem;
  min-width: 230px;
  font-family: inherit;
}

.amap-info-window h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
}

.amap-info-window table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.amap-info-window td {
  padding: 3px 6px;
  color: #475569;
}

.amap-info-window td:first-child {
  color: #94a3b8;
  white-space: nowrap;
}

.amap-info-link {
  display: inline-block;
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #3b82f6;
  text-decoration: none;
}

.amap-info-link:hover {
  text-decoration: underline;
}
</style>
