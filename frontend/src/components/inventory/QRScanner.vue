<template>
  <div class="qr-scanner">
    <div class="scanner-container">
      <div
        v-if="!scanning"
        class="scanner-placeholder"
      >
        <el-icon :size="50">
          <Camera />
        </el-icon>
        <p>点击开始扫描</p>
        <el-button
          type="primary"
          @click="startScan"
        >
          开启摄像头
        </el-button>
      </div>
      <div
        v-else
        class="scanning-view"
      >
        <div class="mock-camera">
          <div class="scan-line" />
        </div>
        <p>正在扫描... (模拟)</p>
        <div class="mock-actions">
          <el-input
            v-model="mockCode"
            placeholder="输入模拟二维码数据"
            style="width: 200px"
          />
          <el-button
            type="success"
            @click="handleScanSuccess"
          >
            确认扫描
          </el-button>
          <el-button @click="stopScan">
            停止
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Camera } from '@element-plus/icons-vue'

const emit = defineEmits(['result'])

const scanning = ref(false)
const mockCode = ref('')

const startScan = () => {
    scanning.value = true
}

const stopScan = () => {
    scanning.value = false
}

const handleScanSuccess = () => {
    if (mockCode.value) {
        emit('result', mockCode.value)
        scanning.value = false
    }
}
</script>

<style scoped>
.qr-scanner {
    width: 100%;
    height: 300px;
    background: #000;
    display: flex;
    justify-content: center;
    align-items: center;
    color: #fff;
    border-radius: 8px;
    overflow: hidden;
}
.scanner-container {
    text-align: center;
}
.mock-camera {
    width: 200px;
    height: 200px;
    border: 2px solid #fff;
    position: relative;
    margin: 0 auto 20px;
}
.scan-line {
    width: 100%;
    height: 2px;
    background: #0f0;
    position: absolute;
    top: 0;
    animation: scan 2s infinite linear;
}
@keyframes scan {
    0% { top: 0; }
    100% { top: 100%; }
}
.mock-actions {
    display: flex;
    gap: 10px;
    justify-content: center;
}
</style>
