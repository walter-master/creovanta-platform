const state = {
  token: localStorage.getItem('creovanta_token') || '',
  user: null,
  projects: [],
  tasks: [],
  milestones: [],
  products: [],
  cart: [],
  documents: [],
  adminSummary: null,
};

const views = document.querySelectorAll('.view');
const navButtons = document.querySelectorAll('.nav-link, .action-btn, .primary-btn, .secondary-btn');
const authModal = document.getElementById('authModal');
const loginButton = document.getElementById('loginButton');
const logoutButton = document.getElementById('logoutButton');
const userBadge = document.getElementById('userBadge');
const toast = document.getElementById('toast');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const closeAuth = document.getElementById('closeAuth');
const authTabs = document.querySelectorAll('.auth-tab');
const authForms = document.querySelectorAll('.auth-form');
const demoButtons = document.querySelectorAll('.mini-demo');
const taskBoard = document.getElementById('taskBoard');
const projectCount = document.getElementById('projectCount');
const projectProgress = document.getElementById('projectProgress');
const projectMilestones = document.getElementById('projectMilestones');
const productGrid = document.getElementById('productGrid');
const cartItems = document.getElementById('cartItems');
const cartCount = document.getElementById('cartCount');
const cartTotal = document.getElementById('cartTotal');
const checkoutBtn = document.getElementById('checkoutBtn');
const taskForm = document.getElementById('taskForm');
const taskProject = document.getElementById('taskProject');
const projectForm = document.getElementById('projectForm');
const milestoneForm = document.getElementById('milestoneForm');
const milestoneProject = document.getElementById('milestoneProject');
const milestoneList = document.getElementById('milestoneList');
const documentUploadForm = document.getElementById('documentUploadForm');
const documentFileInput = document.getElementById('documentFile');
const documentList = document.getElementById('documentList');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chatMessages');
const metricProjects = document.getElementById('metricProjects');
const adminUsers = document.getElementById('adminUsers');
const adminProjects = document.getElementById('adminProjects');
const adminRevenue = document.getElementById('adminRevenue');
const adminOrders = document.getElementById('adminOrders');

const baseUrl = window.location.origin;

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove('hidden');
  clearTimeout(showToast.timeoutId);
  showToast.timeoutId = setTimeout(() => toast.classList.add('hidden'), 2600);
}

function setActiveView(targetId) {
  views.forEach((view) => {
    view.classList.toggle('active', view.id === targetId);
  });

  document.querySelectorAll('.nav-link').forEach((button) => {
    button.classList.toggle('active', button.dataset.target === targetId);
  });
}

function bindNavigation() {
  navButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.target;
      if (!target) return;
      const isLoggedIn = Boolean(state.token);
      if (!isLoggedIn && target !== 'overview') {
        openAuthModal();
        return;
      }
      if (target === 'admin' && state.user?.role !== 'admin') {
        showToast('Admin access is restricted to administrators.');
        return;
      }
      setActiveView(target);
    });
  });
}

function openAuthModal() {
  if (!authModal) return;
  authModal.classList.remove('hidden');
  authModal.setAttribute('aria-hidden', 'false');
}

function closeAuthModal() {
  if (!authModal) return;
  authModal.classList.add('hidden');
  authModal.setAttribute('aria-hidden', 'true');
}

function updateAuthUI() {
  const isLoggedIn = Boolean(state.token && state.user);
  if (loginButton) loginButton.classList.toggle('hidden', isLoggedIn);
  if (logoutButton) logoutButton.classList.toggle('hidden', !isLoggedIn);
  if (userBadge) {
    userBadge.textContent = isLoggedIn ? `Hi, ${state.user.name.split(' ')[0]}` : '';
    userBadge.classList.toggle('hidden', !isLoggedIn);
  }
  const adminNav = document.querySelector('[data-target="admin"]');
  if (adminNav) adminNav.classList.toggle('hidden', !isLoggedIn || state.user.role !== 'admin');
}

function storeToken(token) {
  state.token = token;
  localStorage.setItem('creovanta_token', token);
  updateAuthUI();
}

function clearAuth() {
  state.token = '';
  state.user = null;
  localStorage.removeItem('creovanta_token');
  updateAuthUI();
  showToast('You have been logged out.');
}

async function apiRequest(path, options = {}) {
  const headers = { ...(options.headers || {}) };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
  }

  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || 'Request failed.');
  }

  return payload;
}

function bindAuthForms() {
  if (loginButton) {
    loginButton.addEventListener('click', openAuthModal);
  }

  if (closeAuth) {
    closeAuth.addEventListener('click', closeAuthModal);
  }

  authModal?.addEventListener('click', (event) => {
    if (event.target === authModal) closeAuthModal();
  });

  authTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const mode = tab.dataset.auth;
      authTabs.forEach((button) => button.classList.toggle('active', button === tab));
      authForms.forEach((form) => form.classList.toggle('active', form.id === `${mode}Form`));
    });
  });

  loginForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();

    try {
      const data = await apiRequest('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      state.user = data.user;
      storeToken(data.token);
      closeAuthModal();
      showToast('Welcome back.');
      await loadDashboard();
    } catch (error) {
      showToast(error.message);
    }
  });

  registerForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const fullName = document.getElementById('registerName').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value.trim();

    try {
      const data = await apiRequest('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ full_name: fullName, email, password }),
      });
      state.user = data.user;
      storeToken(data.token);
      closeAuthModal();
      showToast('Account created successfully.');
      await loadDashboard();
    } catch (error) {
      showToast(error.message);
    }
  });

  demoButtons.forEach((button) => {
    button.addEventListener('click', async () => {
      const demo = button.dataset.demo;
      const demoCredentials = {
        engineer: { email: 'engineer@creovanta.io', password: 'Engineer@123' },
        reviewer: { email: 'reviewer@creovanta.io', password: 'Reviewer@123' },
        admin: { email: 'admin@creovanta.io', password: 'Admin@123' },
      };
      const payload = demoCredentials[demo] || demoCredentials.engineer;

      try {
        const data = await apiRequest('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        state.user = data.user;
        storeToken(data.token);
        closeAuthModal();
        showToast(demo === 'admin' ? 'Admin demo session active.' : demo === 'reviewer' ? 'Reviewer demo session active.' : 'Engineer demo session active.');
        await loadDashboard();
      } catch (error) {
        showToast(error.message);
      }
    });
  });

  logoutButton?.addEventListener('click', () => {
    clearAuth();
    setActiveView('overview');
  });
}

function renderChatMessages(messages) {
  if (!chatMessages) return;
  chatMessages.innerHTML = messages.map((message) => `
    <div class="message ${message.sender}">
      <span>${message.sender === 'bot' ? 'AI' : 'You'}</span>
      <p>${message.text}</p>
    </div>
  `).join('');
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function seedChat() {
  renderChatMessages([
    {
      sender: 'bot',
      text: 'Welcome back. I can help with engineering design, PLC logic, industrial automation, AI workflows, and product strategy.',
    },
    {
      sender: 'user',
      text: 'Design a compact AI-assisted maintenance workflow for a packaging line.',
    },
    {
      sender: 'bot',
      text: 'Start with sensor health checks, PLC alarm prioritisation, predictive maintenance thresholds, and a digital checklist. Then add AI summaries for root-cause suggestions and a weekly review dashboard.',
    },
  ]);
}

async function handleChatSubmit(event) {
  event.preventDefault();
  if (!chatInput || !state.token) {
    openAuthModal();
    return;
  }

  const value = chatInput.value.trim();
  if (!value) return;

  const currentMessages = Array.from(document.querySelectorAll('#chatMessages .message')).map((node) => ({
    sender: node.classList.contains('user') ? 'user' : 'bot',
    text: node.querySelector('p')?.textContent || '',
  }));

  currentMessages.push({ sender: 'user', text: value });
  renderChatMessages(currentMessages);
  chatInput.value = '';

  try {
    const data = await apiRequest('/api/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message: value }),
    });
    currentMessages.push({ sender: 'bot', text: data.reply });
    renderChatMessages(currentMessages);
  } catch (error) {
    currentMessages.push({ sender: 'bot', text: 'AI service temporarily unavailable. Please try again.' });
    renderChatMessages(currentMessages);
    showToast(error.message);
  }
}

async function loadProducts() {
  try {
    const data = await apiRequest('/api/products');
    state.products = data.products || [];
    renderProducts();
  } catch (error) {
    showToast(error.message);
  }
}

function renderProducts() {
  if (!productGrid) return;
  productGrid.innerHTML = state.products.map((product) => `
    <article class="product-card">
      <div class="product-badge">${product.category}</div>
      <div class="module-icon">${product.image || '🛍️'}</div>
      <h3>${product.name}</h3>
      <p>${product.description || 'Engineering product'}</p>
      <div class="product-rating">★★★★★ <span>${product.rating}</span></div>
      <div class="product-footer">
        <strong>$${Number(product.price).toFixed(2)}</strong>
        <button class="mini-btn" data-product-id="${product.id}">Add to cart</button>
      </div>
    </article>
  `).join('');

  document.querySelectorAll('.mini-btn').forEach((button) => {
    button.addEventListener('click', () => {
      const productId = Number(button.dataset.productId);
      const product = state.products.find((entry) => entry.id === productId);
      if (!product) return;
      state.cart.push(product);
      renderCart();
      showToast(`${product.name} added to cart.`);
    });
  });
}

function renderCart() {
  if (!cartItems || !cartCount || !cartTotal) return;

  if (!state.cart.length) {
    cartItems.innerHTML = '<p class="empty-cart">Your cart is empty.</p>';
    cartCount.textContent = 'Cart: 0';
    cartTotal.textContent = '$0.00';
    return;
  }

  cartItems.innerHTML = state.cart.map((item) => `
    <div class="cart-item">
      <span>${item.name}</span>
      <strong>$${Number(item.price).toFixed(2)}</strong>
    </div>
  `).join('');

  const total = state.cart.reduce((sum, item) => sum + Number(item.price), 0);
  cartCount.textContent = `Cart: ${state.cart.length}`;
  cartTotal.textContent = `$${total.toFixed(2)}`;
}

checkoutBtn?.addEventListener('click', async () => {
  if (!state.token) {
    openAuthModal();
    return;
  }
  if (!state.cart.length) {
    showToast('Add a product before checkout.');
    return;
  }

  try {
    const data = await apiRequest('/api/checkout/create-session', {
      method: 'POST',
      body: JSON.stringify({ items: state.cart }),
    });

    if (data.checkoutUrl) {
      window.location.href = data.checkoutUrl;
      return;
    }

    state.cart = [];
    renderCart();
    showToast(data.message || 'Checkout complete. Your order is being processed.');
  } catch (error) {
    showToast(error.message);
  }
});

function renderDocuments() {
  if (!documentList) return;

  if (!state.documents.length) {
    documentList.innerHTML = '<p class="empty-cart">No documents uploaded yet.</p>';
    return;
  }

  documentList.innerHTML = state.documents.map((document) => `
    <div class="cart-item">
      <span>${document.original_name}</span>
      <a href="${document.download_url}" target="_blank" rel="noreferrer">Download</a>
    </div>
  `).join('');
}

async function loadDocuments() {
  if (!state.token) {
    state.documents = [];
    renderDocuments();
    return;
  }

  try {
    const data = await apiRequest('/api/documents');
    state.documents = data.documents || [];
    renderDocuments();
  } catch (error) {
    console.error(error);
  }
}

async function uploadDocument(event) {
  event.preventDefault();
  if (!state.token) {
    openAuthModal();
    return;
  }

  const file = documentFileInput?.files?.[0];
  if (!file) {
    showToast('Choose a file to upload.');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${baseUrl}/api/documents/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${state.token}`,
      },
      body: formData,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error || 'Upload failed.');
    }
    documentUploadForm?.reset();
    await loadDocuments();
    showToast('Document uploaded successfully.');
  } catch (error) {
    showToast(error.message);
  }
}

async function loadProjects() {
  if (!state.token) {
    state.projects = [];
    renderTasks();
    return;
  }

  try {
    const data = await apiRequest('/api/projects');
    state.projects = data.projects || [];
    const projectProgressValue = state.projects.length
      ? Math.round(state.projects.reduce((sum, project) => sum + Number(project.progress || 0), 0) / state.projects.length)
      : 0;
    if (projectProgress) projectProgress.textContent = `${projectProgressValue}%`;
    if (metricProjects) metricProjects.textContent = String(state.projects.length);
    const projectOptions = state.projects.map((project) => `<option value="${project.id}">${project.name}</option>`).join('');
    if (taskProject) taskProject.innerHTML = `<option value="">Select project</option>${projectOptions}`;
    if (milestoneProject) milestoneProject.innerHTML = `<option value="">Select project</option>${projectOptions}`;
    renderTasks();
  } catch (error) {
    showToast(error.message);
  }
}

async function loadTasks() {
  if (!state.token) {
    state.tasks = [];
    renderTasks();
    return;
  }

  try {
    const data = await apiRequest('/api/tasks');
    state.tasks = data.tasks || [];
    renderTasks();
  } catch (error) {
    showToast(error.message);
  }
}

function renderTasks() {
  if (!taskBoard) return;
  taskBoard.innerHTML = state.tasks.length ? state.tasks.map((task) => `
    <div class="task-card">
      <div>
        <h4>${task.title}</h4>
        <p>${task.owner || 'Crew'}</p>
      </div>
      <span class="task-status">${task.status || 'Queued'}</span>
    </div>
  `).join('') : '<div class="empty-state"><strong>No tasks yet</strong><span>Create a project, then add its first task.</span></div>';

  if (projectCount) {
    projectCount.textContent = String(state.tasks.filter((task) => !['done', 'complete', 'completed'].includes(String(task.status).toLowerCase())).length);
  }

  if (projectMilestones) {
    projectMilestones.textContent = String(state.milestones?.length || 0);
  }
}

async function loadMilestones() {
  if (!state.token) {
    state.milestones = [];
    renderMilestones();
    return;
  }
  try {
    const data = await apiRequest('/api/milestones');
    state.milestones = data.milestones || [];
    renderMilestones();
    if (projectMilestones) projectMilestones.textContent = String(state.milestones.length);
  } catch (error) {
    showToast(error.message);
  }
}

function renderMilestones() {
  if (!milestoneList) return;
  milestoneList.innerHTML = state.milestones?.length
    ? state.milestones.map((milestone) => `<div class="cart-item"><span>${milestone.title}</span><strong>${milestone.progress}%</strong></div>`).join('')
    : '<p class="empty-cart">No milestones yet.</p>';
}

async function createProject(event) {
  event.preventDefault();
  if (!state.token) {
    openAuthModal();
    return;
  }

  const name = document.getElementById('projectName').value.trim();
  const description = document.getElementById('projectDescription').value.trim();
  const category = document.getElementById('projectCategory').value;

  try {
    await apiRequest('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ name, description, category }),
    });
    document.getElementById('projectForm').reset();
    await loadProjects();
    await loadTasks();
    showToast('Project saved successfully.');
  } catch (error) {
    showToast(error.message);
  }
}

async function createTask(event) {
  event.preventDefault();
  if (!state.token) {
    openAuthModal();
    return;
  }

  const title = document.getElementById('taskTitle').value.trim();
  const projectId = Number(taskProject?.value);
  if (!title || !projectId) {
    showToast('Choose a project before adding a task.');
    return;
  }

  try {
    await apiRequest('/api/tasks', {
      method: 'POST',
      body: JSON.stringify({ title, project_id: projectId, status: 'Queued', owner: state.user?.name || 'You' }),
    });
    document.getElementById('taskTitle').value = '';
    await loadTasks();
    showToast('Task added to workspace.');
  } catch (error) {
    showToast(error.message);
  }

}

async function createMilestone(event) {
  event.preventDefault();
  if (!state.token) {
    openAuthModal();
    return;
  }
  const title = document.getElementById('milestoneTitle').value.trim();
  const projectId = Number(milestoneProject?.value);
  if (!title || !projectId) {
    showToast('Choose a project before adding a milestone.');
    return;
  }
  try {
    await apiRequest('/api/milestones', {
      method: 'POST',
      body: JSON.stringify({ title, project_id: projectId }),
    });
    milestoneForm.reset();
    await Promise.all([loadProjects(), loadMilestones()]);
    showToast('Milestone added.');
  } catch (error) {
    showToast(error.message);
  }
}

async function loadAdminDashboard() {
if (!state.token || state.user?.role !== 'admin') {
    return;
  }

  try {
    const data = await apiRequest('/api/admin/summary');
    state.adminSummary = data;
    const metrics = data.metrics || {};
    adminUsers.textContent = metrics.totalUsers || 0;
    adminProjects.textContent = metrics.totalProjects || 0;
    adminRevenue.textContent = `$${Number(metrics.revenue || 0).toFixed(2)}`;
    adminOrders.textContent = metrics.orders || 0;
  } catch (error) {
    showToast(error.message);
  }
}

async function loadCurrentUser() {
  if (!state.token) {
    updateAuthUI();
    seedChat();
    renderCart();
    return;
  }

  try {
    const data = await apiRequest('/api/auth/me');
    state.user = data.user;
    updateAuthUI();
    await loadDashboard();
  } catch (error) {
    clearAuth();
    showToast('Session expired. Please sign in again.');
  }
}

async function loadDashboard() {
  await Promise.all([loadProjects(), loadTasks(), loadMilestones(), loadProducts(), loadAdminDashboard(), loadDocuments()]);
  renderCart();
  if (state.user && state.user.role === 'admin') {
    setActiveView('admin');
  }
}

function init() {
  bindNavigation();
  bindAuthForms();
  if (documentUploadForm) documentUploadForm.addEventListener('submit', uploadDocument);
  if (chatForm) chatForm.addEventListener('submit', handleChatSubmit);
  if (taskForm) taskForm.addEventListener('submit', createTask);
  if (projectForm) projectForm.addEventListener('submit', createProject);
  if (milestoneForm) milestoneForm.addEventListener('submit', createMilestone);
  if (state.token) {
    loadCurrentUser();
  } else {
    updateAuthUI();
    seedChat();
    renderCart();
    renderDocuments();
  }
}

init();
