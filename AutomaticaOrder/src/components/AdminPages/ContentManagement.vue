<template>
  <section class="content-admin">
    <div v-if="!isAdminOrSuper" class="alert-card">
      <div class="alert">无权限：当前账号无权访问内容管理。</div>
      <div class="row" style="margin-top:10px;">
        <a class="btn" href="/#/">返回首页</a>
      </div>
    </div>

    <template v-else>
      <div class="content-card">
        <div class="toolbar">
          <div class="toolbar-title">内容管理</div>
          <div class="toolbar-actions">
            <span class="muted">最近更新：{{ lastUpdated }}</span>
            <button class="btn-outline" @click="openHistory">历史版本</button>
          </div>
        </div>

        <div class="form-grid">
          <label class="title-field">标题
            <input class="input" v-model="bulletinTitle" placeholder="如：重要通知" />
          </label>
          <label class="content-field">公告内容
            <textarea class="input" v-model="bulletinHtml" @input="updatePreview" placeholder="支持 HTML 富文本与图片 &lt;img&gt; 标签"></textarea>
          </label>
        </div>

        <div class="preview">
          <div class="subtitle">预览</div>
          <div class="preview-box" v-html="bulletinPreview"></div>
        </div>

        <div class="contacts-section">
          <div class="section-header">
            <div class="subtitle">联系方式</div>
            <button class="btn-outline" type="button" @click="addContact">新增项</button>
          </div>
          <transition-group name="contact-row" tag="div" class="contacts-grid">
            <div v-for="(contact, index) in contacts" :key="contact.uid" class="contact-row">
              <select class="input icon-select" v-model="contact.icon">
                <option v-for="option in contactOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
              <input class="input label-input" v-model="contact.label" placeholder="标签，如 微信客服" />
              <input class="input value-input" v-model="contact.value" placeholder="展示信息，如 wenxc-support" />
              <input class="input href-input" v-model="contact.href" placeholder="链接（可选，如 tel: 或 https://）" />
              <button class="btn-danger remove-btn" type="button" @click="removeContact(index)">移除</button>
            </div>
          </transition-group>
          <div v-if="contacts.length === 0" class="muted empty-tip">尚未添加联系方式，点击“新增项”开始配置。</div>
        </div>

        <div class="invites-section">
          <div class="section-header">
            <div class="subtitle">注册码</div>
            <button class="btn-outline" type="button" @click="addInvite">新增邀请码</button>
          </div>
          <transition-group name="invite-row" tag="div" class="invites-grid">
            <div v-for="(code, index) in inviteCodes" :key="`invite-${index}-${code}`" class="invite-row">
              <input class="input invite-input" v-model="inviteCodes[index]" placeholder="请输入邀请码" />
              <button class="btn-danger remove-btn" type="button" @click="removeInvite(index)" :disabled="inviteCodes.length === 1">移除</button>
            </div>
          </transition-group>
        </div>

        <div class="actions">
          <button class="btn-outline" type="button" @click="resetForm">重置</button>
          <button class="btn-gradient-text" type="button" @click="saveBulletin">保存更新</button>
        </div>

        <div v-if="msg" class="status-text">{{ msg }}</div>
      </div>
    </template>

    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="historyState.visible" class="modal-overlay" @click.self="closeHistory">
          <div class="modal-card">
            <h3 class="modal-title">历史版本</h3>
            <div class="history-wrap">
              <table class="history-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>标题</th>
                    <th>创建日期</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="entry in bulletinHistory" :key="entry.id">
                    <td>{{ entry.id }}</td>
                    <td>{{ entry.title || '（无标题）' }}</td>
                    <td>{{ formatDateCn(entry.created_at) }}</td>
                    <td class="history-actions">
                      <button class="btn-outline" @click="loadHistoryEntry(entry.id)">载入</button>
                      <button class="btn-danger" @click="confirmRevert(entry.id)">恢复为当前</button>
                    </td>
                  </tr>
                  <tr v-if="bulletinHistory.length === 0">
                    <td colspan="4" class="empty">暂无历史记录</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="modal-actions">
              <button class="btn-gradient-text" type="button" @click="closeHistory">关闭</button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>

    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="revertState.visible" class="modal-overlay" @click.self="closeRevert">
          <div class="confirm-card">
            <h3 class="modal-title">恢复为当前</h3>
            <p class="modal-tip">确认后将以所选历史版本覆盖当前公告内容，操作不可撤销。</p>
            <div class="modal-actions">
              <button class="btn-outline" type="button" @click="closeRevert" :disabled="revertState.loading">取消</button>
              <button class="btn-gradient-text" type="button" @click="performRevert" :disabled="revertState.loading">
                {{ revertState.loading ? '恢复中…' : '确认恢复' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { adminApi, getRole } from '../../composables/useAdminApi';
import { formatDateCn } from '../../utils/date';
import { useNotifier } from '../../composables/useNotifier';
import { setSiteContacts } from '../../composables/useSiteMeta';

interface ContactItem {
  uid: string;
  icon: string;
  label: string;
  value: string;
  href: string;
}

const contactOptions = [
  { value: 'wechat', label: '微信' },
  { value: 'phone', label: '电话' },
  { value: 'mail', label: '邮箱' },
  { value: 'custom', label: '自定义' },
];

const { showNotice } = useNotifier();
const adminRole = getRole() || '';
const isAdminOrSuper = adminRole === 'admin' || adminRole === 'superadmin';

const bulletinTitle = ref('');
const bulletinHtml = ref('');
const bulletinPreview = ref('');
const bulletinHistory = ref<Array<{ id: number; title: string; html: string; contacts?: unknown; invite_codes?: unknown; created_at: string }>>([]);
const lastUpdated = ref('—');
const msg = ref('');
const contacts = ref<ContactItem[]>([]);
const inviteCodes = ref<string[]>([]);

const historyState = reactive({ visible: false });
const revertState = reactive({ visible: false, targetId: 0, loading: false });
let originalTitle = '';
let originalHtml = '';
let originalContacts: ContactItem[] = [];
let originalInvites: string[] = [];

function makeUid() {
  return `c_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
}

function normalizeContact(raw: Record<string, unknown>): ContactItem {
  return {
    uid: makeUid(),
    icon: String(raw?.icon || 'custom'),
    label: String(raw?.label || ''),
    value: String(raw?.value || ''),
    href: String(raw?.href || ''),
  };
}

function cloneContacts(items: ContactItem[] | Array<Record<string, unknown>>) {
  if (!Array.isArray(items)) return [] as ContactItem[];
  return items.map(item => normalizeContact(item as Record<string, unknown>));
}

function sanitizeHtml(html: string) {
  try {
    const tmp = document.createElement('div');
    tmp.innerHTML = html || '';
    tmp.querySelectorAll('script').forEach(node => node.remove());
    return tmp.innerHTML;
  } catch {
    return html || '';
  }
}

function updatePreview() {
  bulletinPreview.value = sanitizeHtml(bulletinHtml.value);
}

function addContact() {
  contacts.value.push({ uid: makeUid(), icon: 'custom', label: '', value: '', href: '' });
}

function removeContact(index: number) {
  contacts.value.splice(index, 1);
}

function addInvite() {
  inviteCodes.value.push('');
}

function removeInvite(index: number) {
  inviteCodes.value.splice(index, 1);
  if (inviteCodes.value.length === 0) inviteCodes.value.push('');
}

function resetForm() {
  bulletinTitle.value = originalTitle;
  bulletinHtml.value = originalHtml;
  contacts.value = cloneContacts(originalContacts);
  inviteCodes.value = [...originalInvites];
  if (inviteCodes.value.length === 0) inviteCodes.value.push('');
  updatePreview();
  msg.value = '';
}

function serializeContacts() {
  return contacts.value
    .map(item => ({
      icon: item.icon,
      label: item.label.trim(),
      value: item.value.trim(),
      href: item.href.trim(),
    }))
    .filter(item => item.label || item.value || item.href);
}

function serializeInvites() {
  return inviteCodes.value
    .map(code => (code || '').trim())
    .filter(code => !!code);
}

async function loadBulletin() {
  try {
    const data = await adminApi.getAnnouncement();
    bulletinTitle.value = (data && data.title) || '公告栏';
    bulletinHtml.value = (data && data.html) || '';
    contacts.value = cloneContacts((data && data.contacts) || []);
    const invites = Array.isArray(data?.invite_codes) ? data.invite_codes.map((code: unknown) => String(code || '')) : [];
    inviteCodes.value = invites.length ? invites : [''];
    originalTitle = bulletinTitle.value;
    originalHtml = bulletinHtml.value;
    originalContacts = cloneContacts(contacts.value);
    originalInvites = [...inviteCodes.value];
    updatePreview();
    if (data && data.updated_at) {
      lastUpdated.value = formatDateCn(data.updated_at);
    }
    const history = await adminApi.getAnnouncementHistory(50);
    bulletinHistory.value = (history && history.items) || [];
    setSiteContacts(serializeContacts());
    msg.value = '';
  } catch (error) {
    const message = (error && (error as Error).message) || '加载公告失败';
    msg.value = message;
    showNotice({ type: 'error', message });
  }
}

async function saveBulletin() {
  msg.value = '保存中…';
  try {
    const payload = {
      title: bulletinTitle.value,
      html: bulletinHtml.value,
      contacts: serializeContacts(),
      invite_codes: serializeInvites(),
    };
    await adminApi.saveAnnouncement(payload);
    msg.value = '公告已保存';
    showNotice({ type: 'success', message: '公告已保存' });
    setSiteContacts(payload.contacts);
    await loadBulletin();
  } catch (error) {
    const message = (error && (error as Error).message) || '保存失败';
    msg.value = message;
    showNotice({ type: 'error', message });
  }
}

function openHistory() {
  historyState.visible = true;
}

function closeHistory() {
  historyState.visible = false;
}

function loadHistoryEntry(id: number) {
  const entry = bulletinHistory.value.find(item => item.id === id);
  if (!entry) return;
  bulletinTitle.value = entry.title || '公告栏';
  bulletinHtml.value = entry.html || '';
  if ('contacts' in entry && entry.contacts) {
    contacts.value = cloneContacts(entry.contacts as ContactItem[] | Array<Record<string, unknown>>);
  }
  if ('invite_codes' in entry && Array.isArray(entry.invite_codes)) {
    const list = (entry.invite_codes as Array<unknown>).map(code => String(code || '')).filter(Boolean);
    inviteCodes.value = list.length ? list : [''];
  }
  updatePreview();
  closeHistory();
}

function confirmRevert(id: number) {
  if (!id) return;
  revertState.visible = true;
  revertState.targetId = id;
  revertState.loading = false;
}

function closeRevert() {
  if (revertState.loading) return;
  revertState.visible = false;
  revertState.targetId = 0;
}

async function performRevert() {
  if (!revertState.targetId) {
    closeRevert();
    return;
  }
  revertState.loading = true;
  msg.value = '恢复中…';
  try {
    await adminApi.revertAnnouncement(revertState.targetId);
    msg.value = '已恢复为所选版本';
    showNotice({ type: 'success', message: '已恢复为所选版本' });
    await loadBulletin();
    closeHistory();
    closeRevert();
  } catch (error) {
    const message = (error && (error as Error).message) || '恢复失败';
    msg.value = message;
    showNotice({ type: 'error', message });
  } finally {
    revertState.loading = false;
  }
}

const historyCount = computed(() => bulletinHistory.value.length);

onMounted(() => {
  if (isAdminOrSuper) {
    loadBulletin();
  }
});
</script>

<style scoped>
.content-admin { display: flex; flex-direction: column; gap: 18px; }
.row { display: flex; align-items: center; gap: 10px; }

.alert-card {
  background: rgba(9, 16, 28, 0.62);
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 20px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  backdrop-filter: blur(16px) saturate(1.35);
  -webkit-backdrop-filter: blur(16px) saturate(1.35);
  box-shadow: 0 22px 42px rgba(0, 0, 0, 0.32);
}

.alert {
  color: #ffe9be;
  background: rgba(255, 183, 77, 0.12);
  border: 1px solid rgba(255, 183, 77, 0.32);
  padding: 12px 14px;
  border-radius: 12px;
}

.btn,
.btn-outline,
.btn-gradient-text,
.btn-danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  border-radius: 12px;
  padding: 0 16px;
  cursor: pointer;
  font-weight: 600;
  letter-spacing: 0.3px;
  transition: transform 180ms ease, box-shadow 220ms ease, background 220ms ease, border-color 220ms ease, color 220ms ease;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.btn {
  background: linear-gradient(135deg, rgba(22, 41, 72, 0.48), rgba(10, 24, 44, 0.42));
  border: 1px solid rgba(148, 176, 215, 0.32);
  color: #dbeafe;
}
.btn:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.32), rgba(14, 32, 58, 0.48));
  border-color: rgba(148, 205, 255, 0.52);
  box-shadow: 0 16px 32px rgba(37, 99, 235, 0.28);
  color: #f8fbff;
}

.btn-outline {
  background: linear-gradient(135deg, rgba(16, 45, 88, 0.32), rgba(10, 20, 38, 0.46));
  border: 1px solid rgba(148, 205, 255, 0.38);
  color: #e1efff;
}
.btn-outline:hover:not(:disabled) {
  transform: translateY(-1px);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.38), rgba(37, 211, 164, 0.26));
  border-color: rgba(148, 205, 255, 0.6);
  box-shadow: 0 18px 36px rgba(30, 90, 180, 0.32);
  color: #0b172a;
}

.btn-gradient-text {
  background: linear-gradient(135deg, rgba(39, 255, 160, 0.7), rgba(126, 243, 255, 0.68));
  border: 1px solid rgba(148, 255, 225, 0.28);
  color: #052032;
  box-shadow: 0 18px 34px rgba(20, 200, 160, 0.28);
}
.btn-gradient-text:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 22px 42px rgba(20, 200, 160, 0.36);
}

.btn-danger {
  background: linear-gradient(135deg, rgba(140, 32, 32, 0.45), rgba(75, 18, 27, 0.55));
  border: 1px solid rgba(255, 149, 149, 0.48);
  color: #ffe4e6;
}
.btn-danger:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(255, 149, 149, 0.68);
  box-shadow: 0 16px 32px rgba(120, 32, 46, 0.36);
}

.btn[disabled],
.btn-outline[disabled],
.btn-gradient-text[disabled],
.btn-danger[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.content-card {
  background: rgba(9, 16, 28, 0.66);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 24px;
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  backdrop-filter: blur(20px) saturate(1.35);
  -webkit-backdrop-filter: blur(20px) saturate(1.35);
  box-shadow: 0 24px 46px rgba(0, 0, 0, 0.38);
}

.toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
}

.toolbar-title {
  font-size: 1.12rem;
  font-weight: 700;
  letter-spacing: 0.6px;
  color: #f4f8ff;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.muted { color: rgba(204, 213, 235, 0.76); font-size: 0.9rem; }

.form-grid { display: grid; grid-template-columns: repeat(1, minmax(0, 1fr)); gap: 18px; }
.title-field .input { max-width: 420px; }
.content-field textarea { min-height: 180px; resize: vertical; }

.contacts-section,
.invites-section {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.contacts-grid,
.invites-grid { display: flex; flex-direction: column; gap: 10px; }

.contact-row {
  display: grid;
  grid-template-columns: minmax(90px, 120px) minmax(140px, 1fr) minmax(160px, 1fr) minmax(200px, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(12, 22, 40, 0.46);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.invite-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(12, 22, 40, 0.46);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.icon-select,
.label-input,
.value-input,
.href-input,
.invite-input { width: 100%; }

.remove-btn { min-width: 88px; justify-self: end; }
.empty-tip { font-size: 0.88rem; color: rgba(204, 213, 235, 0.72); }

.preview { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.subtitle { font-weight: 600; color: rgba(203, 214, 235, 0.9); }
.preview-box {
  background: rgba(9, 12, 20, 0.75);
  border: 1px solid rgba(86, 104, 139, 0.45);
  border-radius: 14px;
  padding: 16px;
  min-height: 120px;
  color: #f3f6ff;
  line-height: 1.6;
}

.actions { margin-top: 12px; display: flex; gap: 12px; justify-content: flex-end; }
.status-text { margin-top: 8px; color: rgba(199, 210, 228, 0.78); font-size: 0.88rem; }

.contact-row-enter-active,
.contact-row-leave-active,
.invite-row-enter-active,
.invite-row-leave-active { transition: opacity 220ms ease, transform 220ms ease; }
.contact-row-enter-from,
.contact-row-leave-to,
.invite-row-enter-from,
.invite-row-leave-to { opacity: 0; transform: translateY(-6px); }

.modal-fade-enter-active,
.modal-fade-leave-active { transition: opacity 220ms ease; }
.modal-fade-enter-from,
.modal-fade-leave-to { opacity: 0; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 10, 18, 0.68);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 9999;
}

.modal-card {
  width: min(640px, 96vw);
  background: rgba(15, 20, 32, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.45);
}

.modal-title { margin: 0; font-size: 1.2rem; font-weight: 700; color: #f1f5ff; }
.modal-tip { color: rgba(204, 213, 235, 0.8); }
.modal-message { color: rgba(139, 215, 255, 0.82); }
.modal-stats { display: grid; gap: 6px; color: rgba(226, 238, 255, 0.92); }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; }

.history-wrap { max-height: 360px; overflow: auto; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); }
.history-table { width: 100%; border-collapse: collapse; }
.history-table th,
.history-table td { padding: 10px 12px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.08); }
.history-table th { color: #aeb7c9; font-size: 0.92rem; }
.history-table td { color: #e7ecf8; font-size: 0.9rem; }
.history-actions { display: flex; gap: 8px; }
.empty { text-align: center; padding: 32px 0; color: rgba(199, 206, 224, 0.75); }

.confirm-card {
  width: min(420px, 92vw);
  background: rgba(12, 22, 40, 0.9);
  border: 1px solid rgba(102, 212, 255, 0.38);
  border-radius: 20px;
  padding: 24px 26px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  box-shadow: 0 24px 46px rgba(0, 0, 0, 0.42);
}

@media (max-width: 1024px) {
  .contact-row { grid-template-columns: minmax(90px, 1fr) repeat(3, minmax(0, 1fr)); }
  .remove-btn { justify-self: stretch; }
}

@media (max-width: 800px) {
  .toolbar-actions { flex-direction: column; align-items: flex-start; gap: 10px; }
  .actions { flex-direction: column; align-items: stretch; }
}

@media (max-width: 640px) {
  .content-card { padding: 18px; }
  .contact-row { grid-template-columns: repeat(1, minmax(0, 1fr)); }
  .invite-row { grid-template-columns: repeat(1, minmax(0, 1fr)); }
  .modal-card { padding: 20px 22px; }
}
</style>
