// 管理员后台页面逻辑

// 加载用户列表
async function loadUsers() {
    try {
        const response = await fetch('/api/admin/users');
        const data = await response.json();
        
        if (data.success) {
            displayUsers(data.users);
            updateStats(data.users);
        } else {
            console.error('加载用户列表失败:', data.error);
        }
    } catch (error) {
        console.error('网络错误:', error);
    } finally {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('users-table').style.display = 'table';
    }
}

// 显示用户列表
function displayUsers(users) {
    const tbody = document.getElementById('users-tbody');
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email || '-'}</td>
            <td>
                <span class="role-badge role-${user.role}">${user.role === 'admin' ? '管理员' : '普通用户'}</span>
            </td>
            <td>${user.created_at ? new Date(user.created_at).toLocaleString('zh-CN') : '-'}</td>
            <td>${user.last_login ? new Date(user.last_login).toLocaleString('zh-CN') : '从未登录'}</td>
            <td>
                <button class="action-btn btn-edit" onclick="changeRole(${user.id}, '${user.role}')">
                    ${user.role === 'admin' ? '设为用户' : '设为管理员'}
                </button>
                <button class="action-btn btn-delete" onclick="deleteUser(${user.id})">
                    删除
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 更新统计信息
function updateStats(users) {
    const totalUsers = users.length;
    const adminCount = users.filter(u => u.role === 'admin').length;
    const userCount = users.filter(u => u.role === 'user').length;
    
    document.getElementById('total-users').textContent = totalUsers;
    document.getElementById('admin-count').textContent = adminCount;
    document.getElementById('user-count').textContent = userCount;
}

// 更改用户角色
async function changeRole(userId, currentRole) {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    const confirmMsg = `确定要将该用户${newRole === 'admin' ? '设为管理员' : '设为普通用户'}吗？`;
    
    if (!confirm(confirmMsg)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/user/${userId}/role`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ role: newRole })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('角色更新成功');
            loadUsers(); // 重新加载用户列表
        } else {
            alert('更新失败: ' + data.error);
        }
    } catch (error) {
        alert('网络错误: ' + error.message);
    }
}

// 删除用户
async function deleteUser(userId) {
    if (!confirm('确定要删除该用户吗？此操作不可恢复！')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/user/${userId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('用户删除成功');
            loadUsers(); // 重新加载用户列表
        } else {
            alert('删除失败: ' + data.error);
        }
    } catch (error) {
        alert('网络错误: ' + error.message);
    }
}

// 页面加载时获取用户列表
window.addEventListener('DOMContentLoaded', () => {
    loadUsers();
});
