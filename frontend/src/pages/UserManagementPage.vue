<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Users</p>
        <h3>用户管理</h3>
      </div>
      <p class="section-note">管理员可创建账号、调整角色、启用禁用用户并重置密码。</p>
    </header>

    <div class="content-grid two-columns">
      <PanelCard title="创建用户" subtitle="新增管理员、维修人员或普通用户账号">
        <form class="form-grid" @submit.prevent="handleCreateUser">
          <label>
            <span>用户名</span>
            <input v-model.trim="createForm.username" class="search-input" type="text" />
          </label>
          <label>
            <span>初始密码</span>
            <input v-model="createForm.password" class="search-input" type="password" />
          </label>
          <label>
            <span>角色</span>
            <select v-model="createForm.role" class="search-input">
              <option v-for="role in allRoles" :key="role" :value="role">
                {{ roleLabels[role] }}
              </option>
            </select>
          </label>
          <label class="checkbox-field">
            <input v-model="createForm.is_active" type="checkbox" />
            <span>启用账号</span>
          </label>
          <div class="button-row">
            <button class="primary-button" type="submit" :disabled="saving">
              {{ saving ? "保存中..." : "创建用户" }}
            </button>
            <span class="inline-note">{{ message }}</span>
          </div>
        </form>
      </PanelCard>

      <PanelCard title="权限说明" subtitle="三类账号的功能边界">
        <div class="detail-summary-grid">
          <div class="summary-box">
            <strong>管理员</strong>
            <span>拥有全部页面和全部操作权限，包括用户与模拟器管理。</span>
          </div>
          <div class="summary-box">
            <strong>维修人员</strong>
            <span>可查看数据、处理告警、控制路灯和修改阈值。</span>
          </div>
          <div class="summary-box">
            <strong>普通用户</strong>
            <span>只读查看总览、设备、光照、告警和智能问答。</span>
          </div>
        </div>
      </PanelCard>
    </div>

    <PanelCard title="用户列表" subtitle="修改后立即保存到后端">
      <div class="search-bar">
        <input
          v-model="searchQuery"
          class="search-input"
          type="text"
          placeholder="搜索用户名..."
          @input="handleSearch"
        />
      </div>
      <div v-if="loading" class="placeholder-box">正在加载用户列表...</div>
      <div v-else-if="loadError" class="placeholder-box">{{ loadError }}</div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
              <th>角色</th>
              <th>状态</th>
              <th>重置密码</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.id }}</td>
              <td>
                <input v-model.trim="editForms[user.id].username" class="search-input table-input" type="text" />
              </td>
              <td>
                <select v-model="editForms[user.id].role" class="search-input table-input">
                  <option v-for="role in allRoles" :key="role" :value="role">
                    {{ roleLabels[role] }}
                  </option>
                </select>
              </td>
              <td>
                <label class="checkbox-field table-checkbox">
                  <input v-model="editForms[user.id].is_active" type="checkbox" />
                  <span>{{ editForms[user.id].is_active ? "启用" : "禁用" }}</span>
                </label>
              </td>
              <td>
                <input
                  v-model="editForms[user.id].password"
                  class="search-input table-input"
                  type="password"
                  placeholder="留空则不修改"
                />
              </td>
              <td class="action-cell">
                <button
                  class="primary-button"
                  type="button"
                  :disabled="savingUserId === user.id"
                  @click="handleUpdateUser(user.id)"
                >
                  {{ savingUserId === user.id ? "保存中..." : "保存" }}
                </button>
                <button
                  class="danger-button"
                  type="button"
                  :disabled="deletingUserId === user.id"
                  @click="handleDeleteUser(user)"
                >
                  {{ deletingUserId === user.id ? "删除中..." : "删除" }}
                </button>
              </td>
            </tr>
            <tr v-if="!users.length">
              <td colspan="6" class="table-empty">暂无用户</td>
            </tr>
          </tbody>
        </table>
      </div>
    </PanelCard>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import PanelCard from "@/components/PanelCard.vue";
import { createUser, deleteUser, getUserList, updateUser } from "@/services/api/userService";
import { allRoles, roleLabels } from "@/services/permissions";
import type { AuthUser, UserRole } from "@/types/models";

interface UserEditForm {
  username: string;
  role: UserRole;
  is_active: boolean;
  password: string;
}

const users = ref<AuthUser[]>([]);
const loading = ref(true);
const loadError = ref("");
const saving = ref(false);
const savingUserId = ref<number | null>(null);
const deletingUserId = ref<number | null>(null);
const message = ref("");
const searchQuery = ref("");
let searchTimer: ReturnType<typeof setTimeout> | null = null;

const createForm = reactive({
  username: "",
  password: "",
  role: "user" as UserRole,
  is_active: true,
});

const editForms = reactive<Record<number, UserEditForm>>({});

function getErrorMessage(error: unknown) {
  if (!(error instanceof Error)) return "操作失败，请稍后重试";

  try {
    const parsed = JSON.parse(error.message) as { detail?: string };
    return parsed.detail || error.message;
  } catch {
    return error.message || "操作失败，请稍后重试";
  }
}

function syncEditForms(nextUsers: AuthUser[]) {
  nextUsers.forEach((user) => {
    editForms[user.id] = {
      username: user.username,
      role: user.role,
      is_active: user.is_active ?? true,
      password: "",
    };
  });
}

async function loadUsers() {
  loading.value = true;
  loadError.value = "";
  try {
    users.value = await getUserList(searchQuery.value || undefined);
    syncEditForms(users.value);
  } catch (error) {
    users.value = [];
    loadError.value = getErrorMessage(error);
  } finally {
    loading.value = false;
  }
}

async function handleCreateUser() {
  if (!createForm.username || !createForm.password) {
    message.value = "请输入用户名和初始密码";
    return;
  }

  saving.value = true;
  message.value = "";
  try {
    await createUser({ ...createForm });
    createForm.username = "";
    createForm.password = "";
    createForm.role = "user";
    createForm.is_active = true;
    message.value = "用户已创建";
    await loadUsers();
  } catch (error) {
    message.value = getErrorMessage(error);
  } finally {
    saving.value = false;
  }
}

async function handleUpdateUser(userId: number) {
  const form = editForms[userId];
  if (!form.username) {
    message.value = "用户名不能为空";
    return;
  }

  savingUserId.value = userId;
  message.value = "";
  try {
    await updateUser(userId, {
      username: form.username,
      role: form.role,
      is_active: form.is_active,
      ...(form.password ? { password: form.password } : {}),
    });
    message.value = "用户已更新";
    await loadUsers();
  } catch (error) {
    message.value = getErrorMessage(error);
  } finally {
    savingUserId.value = null;
  }
}

function handleSearch() {
  if (searchTimer !== null) {
    clearTimeout(searchTimer);
  }
  searchTimer = setTimeout(() => {
    void loadUsers();
  }, 300);
}

async function handleDeleteUser(user: AuthUser) {
  if (!confirm(`确定要删除用户 "${user.username}" 吗？此操作不可恢复。`)) {
    return;
  }

  deletingUserId.value = user.id;
  message.value = "";
  try {
    await deleteUser(user.id);
    message.value = `用户 "${user.username}" 已删除`;
    await loadUsers();
  } catch (error) {
    message.value = getErrorMessage(error);
  } finally {
    deletingUserId.value = null;
  }
}

onMounted(() => {
  void loadUsers();
});
</script>

<style scoped>
.search-bar {
  margin-bottom: 12px;
}

.action-cell {
  display: flex;
  gap: 8px;
  align-items: center;
}

.danger-button {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
  background: #e74c3c;
  color: #fff;
}

.danger-button:hover:not(:disabled) {
  background: #c0392b;
}

.danger-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

html[data-theme="dark"] .danger-button {
  background: #e74c3c;
  color: #fff;
}

html[data-theme="dark"] .danger-button:hover:not(:disabled) {
  background: #c0392b;
}
</style>
