const categories = [
  {
    title: 'PLC',
    icon: '⚙️',
    description: 'Programmable logic controllers, industrial control logic, and automation systems.',
    parent: 'mechatronics',
    count: 'Core automation'
  },
  {
    title: 'Sensors',
    icon: '📡',
    description: 'Measurement, condition monitoring, feedback systems, and smart detection.',
    parent: 'mechatronics',
    count: 'Reliable data'
  },
  {
    title: 'Motors',
    icon: '🧲',
    description: 'Drive systems, motion control, AC/DC motors, and electromechanical motion.',
    parent: 'mechatronics',
    count: 'Power & motion'
  },
  {
    title: 'HMI',
    icon: '🖥️',
    description: 'Human-machine interfaces that connect operators to process control systems.',
    parent: 'mechatronics',
    count: 'Operator tools'
  },
  {
    title: 'Pneumatics',
    icon: '💨',
    description: 'Air-powered actuators and systems used in automation and manufacturing lines.',
    parent: 'mechatronics',
    count: 'Efficient motion'
  },
  {
    title: 'Hydraulics',
    icon: '🛢️',
    description: 'High-force fluid power systems used for lifting, pressing, and precision motion.',
    parent: 'mechatronics',
    count: 'Heavy duty'
  },
  {
    title: 'Industrial Networks',
    icon: '🔌',
    description: 'Fieldbus, Ethernet, control communication pathways, and plant connectivity.',
    parent: 'mechatronics',
    count: 'System integration'
  },
  {
    title: 'PET Lines',
    icon: '🏭',
    description: 'High-output production systems for beverage and packaging manufacturing.',
    parent: 'industrial',
    count: 'Plant systems'
  },
  {
    title: 'Filling',
    icon: '🧴',
    description: 'Liquid filling systems, process accuracy, hygiene, and packaging efficiency.',
    parent: 'industrial',
    count: 'Production flow'
  },
  {
    title: 'Blow Molding',
    icon: '🧪',
    description: 'Bottle formation processes and equipment used in packaging production.',
    parent: 'industrial',
    count: 'Forming systems'
  },
  {
    title: 'Packaging',
    icon: '📦',
    description: 'Wrapping, boxing, labeling, and end-of-line automation processes.',
    parent: 'industrial',
    count: 'Logistics ready'
  },
  {
    title: 'Refrigeration',
    icon: '❄️',
    description: 'Thermal systems, cooling cycles, and industrial refrigeration fundamentals.',
    parent: 'industrial',
    count: 'Thermal control'
  },
  {
    title: 'Maintenance',
    icon: '🛠️',
    description: 'Preventive maintenance, diagnostics, uptime strategies, and troubleshooting.',
    parent: 'industrial',
    count: 'Reliability'
  },
  {
    title: 'Troubleshooting',
    icon: '🔎',
    description: 'Root-cause analysis and practical fault-finding for industrial systems.',
    parent: 'industrial',
    count: 'Problem solving'
  },
  {
    title: 'AI for Engineers',
    icon: '🤖',
    description: 'Applying AI to engineering workflows, analysis, optimization, and decision support.',
    parent: 'ai',
    count: 'Smart tools'
  },
  {
    title: 'AI Tools',
    icon: '🧠',
    description: 'Prompting, automation, and practical use of modern AI assistants and tools.',
    parent: 'ai',
    count: 'Modern workflows'
  },
  {
    title: 'Productivity',
    icon: '📈',
    description: 'Streamlining engineering work, reporting, design review, and daily efficiency.',
    parent: 'ai',
    count: 'Efficiency'
  },
  {
    title: 'Automation + AI',
    icon: '⚡',
    description: 'Combined systems where AI and process automation improve output and insight.',
    parent: 'ai',
    count: 'Next-gen systems'
  },
  {
    title: 'Python',
    icon: '🐍',
    description: 'Hands-on scripting, automation, analysis, and engineering-friendly programming.',
    parent: 'coding',
    count: 'Automation script'
  },
  {
    title: 'Web Development',
    icon: '🌐',
    description: 'Frontend and backend web skills used to design and deliver digital tools.',
    parent: 'coding',
    count: 'Build tools'
  },
  {
    title: 'Engineering Programming',
    icon: '🧮',
    description: 'Tools, logic, and coding approaches tailored for technical problem solving.',
    parent: 'coding',
    count: 'Applied code'
  },
  {
    title: 'Automation Software',
    icon: '🛠️',
    description: 'Software systems that automate tasks, reporting, testing, and industrial workflows.',
    parent: 'coding',
    count: 'Workflow efficiency'
  },
  {
    title: 'TVET',
    icon: '🎓',
    description: 'Technical and vocational education pathways for skill-based engineering careers.',
    parent: 'careers',
    count: 'Skill pathways'
  },
  {
    title: 'Engineering Careers',
    icon: '🚀',
    description: 'Career planning, growth opportunities, and success paths in engineering fields.',
    parent: 'careers',
    count: 'Career growth'
  },
  {
    title: 'Attachments',
    icon: '📎',
    description: 'Document templates, technical files, supporting materials, and project attachments.',
    parent: 'careers',
    count: 'Ready to use'
  },
  {
    title: 'CVs',
    icon: '📄',
    description: 'Professional resumes and technical profile writing for engineering opportunities.',
    parent: 'careers',
    count: 'Career readiness'
  },
  {
    title: 'Technical Interviews',
    icon: '🗣️',
    description: 'Preparation for hands-on, technical, and industry-specific interview questions.',
    parent: 'careers',
    count: 'Interview prep'
  },
  {
    title: 'Machines',
    icon: '🦾',
    description: 'How industrial machines are designed, powered, and used in production.',
    parent: 'how-it-works',
    count: 'Mechanical basics'
  },
  {
    title: 'Control Systems',
    icon: '🔁',
    description: 'Feedback loops, logic, actuation, and how systems respond to commands.',
    parent: 'how-it-works',
    count: 'System behavior'
  },
  {
    title: 'Electrical Systems',
    icon: '⚡',
    description: 'Power distribution, wiring, circuits, and electrical understanding fundamentals.',
    parent: 'how-it-works',
    count: 'Power flow'
  },
  {
    title: 'Manufacturing',
    icon: '🏗️',
    description: 'How goods are produced, optimized, and scaled in modern factories.',
    parent: 'how-it-works',
    count: 'Production life cycle'
  }
];

const products = [
  { id: 1, name: 'PLC Programming Toolkit', price: 49, category: 'Automation', rating: 4.9 },
  { id: 2, name: 'Industrial Design Templates', price: 39, category: 'Design', rating: 4.8 },
  { id: 3, name: 'AI Workflow Pack', price: 59, category: 'AI', rating: 5.0 },
  { id: 4, name: 'Electrical Calculators Bundle', price: 29, category: 'Systems', rating: 4.7 },
  { id: 5, name: 'Prototype Documentation Kit', price: 35, category: 'Product', rating: 4.9 },
  { id: 6, name: 'Engineering CV Pack', price: 22, category: 'Career', rating: 4.8 }
];

const tasks = [
  { title: 'Review PLC safety overhauls', status: 'In progress', owner: 'Automation lead' },
  { title: 'Draft AI assistant workflow', status: 'Queued', owner: 'AI team' },
  { title: 'Finalize prototype review deck', status: 'Review', owner: 'Product design' }
];

const grid = document.querySelector('#categoryGrid');
const filterButtons = document.querySelectorAll('.filter-btn');
const ctaForm = document.querySelector('.cta-form');
const navLinks = document.querySelectorAll('.nav-link, .action-btn, .primary-btn, .secondary-btn');
const views = document.querySelectorAll('.view');
const authModal = document.getElementById('authModal');
const loginButton = document.getElementById('loginButton');
const userBadge = document.getElementById('userBadge');
const toast = document.getElementById('toast');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chatMessages');
const taskBoard = document.getElementById('taskBoard');
const projectCount = document.getElementById('projectCount');
const taskForm = document.getElementById('taskForm');
const productGrid = document.getElementById('productGrid');
const cartItems = document.getElementById('cartItems');
const cartCount = document.getElementById('cartCount');
const cartTotal = document.getElementById('cartTotal');
const checkoutBtn = document.getElementById('checkoutBtn');
const authTabs = document.querySelectorAll('.auth-tab');
const authForms = document.querySelectorAll('.auth-form');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const closeAuth = document.getElementById('closeAuth');
const miniDemoButtons = document.querySelectorAll('.mini-demo');

const cart = [];

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove('hidden');
  clearTimeout(showToast.timeoutId);
  showToast.timeoutId = setTimeout(() => toast.classList.add('hidden'), 2200);
}

function renderCategories(filter = 'all') {
  if (!grid) return;

  const visible = categories.filter((item) => filter === 'all' || item.parent === filter);

  grid.innerHTML = visible
    .map(
      (item) => `
        <article class="category-card" data-parent="${item.parent}">
          <div class="category-icon" aria-hidden="true">${item.icon}</div>
          <h3>${item.title}</h3>
          <p>${item.description}</p>
          <div class="card-meta">
            <span>${item.count}</span>
            <span>Explore</span>
          </div>
        </article>
      `
    )
    .join('');
}

function setActiveView(targetId) {
  views.forEach((view) => {
    view.classList.toggle('active', view.id === targetId);
  });

  document.querySelectorAll('.nav-link').forEach((button) => {
    button.classList.toggle('active', button.dataset.target === targetId);
  });
}

function initNavigation() {
  navLinks.forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.target;
      if (!target) return;
      setActiveView(target);
      if (target === 'overview' || target === 'aiWorkspace' || target === 'projects' || target === 'store' || target === 'admin') {
        const targetView = document.getElementById(target);
        if (targetView) targetView.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

function initAuthFlow() {
  if (!loginButton) return;
  const user = JSON.parse(localStorage.getItem('creovanta-user') || 'null');

  if (user) {
    userBadge.textContent = user.name ? `Hi, ${user.name.split(' ')[0]}` : 'Account';
    userBadge.classList.remove('hidden');
    loginButton.classList.add('hidden');
  }

  loginButton.addEventListener('click', () => {
    if (authModal) {
      authModal.classList.remove('hidden');
      authModal.setAttribute('aria-hidden', 'false');
    }
  });

  closeAuth?.addEventListener('click', () => {
    authModal.classList.add('hidden');
    authModal.setAttribute('aria-hidden', 'true');
  });

  authModal?.addEventListener('click', (event) => {
    if (event.target === authModal) {
      authModal.classList.add('hidden');
      authModal.setAttribute('aria-hidden', 'true');
    }
  });

  authTabs.forEach((button) => {
    button.addEventListener('click', () => {
      const mode = button.dataset.auth;
      authTabs.forEach((tab) => tab.classList.toggle('active', tab === button));
      authForms.forEach((form) => {
        form.classList.toggle('active', form.id === `${mode}Form`);
      });
    });
  });

  loginForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();

    if (!email || !password) {
      showToast('Please complete your sign-in details.');
      return;
    }

    const userData = { name: email.includes('admin') ? 'Admin User' : 'Engineer User', email };
    localStorage.setItem('creovanta-user', JSON.stringify(userData));
    userBadge.textContent = `Hi, ${userData.name.split(' ')[0]}`;
    userBadge.classList.remove('hidden');
    loginButton.classList.add('hidden');
    authModal.classList.add('hidden');
    showToast('Signed in successfully.');
  });

  registerForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    const name = document.getElementById('registerName').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value.trim();

    if (!name || !email || !password) {
      showToast('Please complete all fields to create an account.');
      return;
    }

    const userData = { name, email };
    localStorage.setItem('creovanta-user', JSON.stringify(userData));
    userBadge.textContent = `Hi, ${userData.name.split(' ')[0]}`;
    userBadge.classList.remove('hidden');
    loginButton.classList.add('hidden');
    authModal.classList.add('hidden');
    showToast('Account created. Welcome to CREOVANTA.');
  });

  miniDemoButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const demo = button.dataset.demo;
      const userData = demo === 'admin'
        ? { name: 'Admin User', email: 'admin@creovanta.io' }
        : { name: 'Engineer User', email: 'engineer@creovanta.io' };

      localStorage.setItem('creovanta-user', JSON.stringify(userData));
      userBadge.textContent = `Hi, ${userData.name.split(' ')[0]}`;
      userBadge.classList.remove('hidden');
      loginButton.classList.add('hidden');
      authModal.classList.add('hidden');
      showToast(demo === 'admin' ? 'Admin demo session active.' : 'Engineer demo session active.');
    });
  });
}

function renderChat() {
  if (!chatMessages) return;

  const defaultMessages = [
    {
      sender: 'bot',
      text: 'Welcome back. I can help with engineering design, PLC logic, industrial automation, AI workflows, and product strategy.'
    },
    {
      sender: 'user',
      text: 'Design a compact AI-assisted maintenance workflow for a packaging line.'
    },
    {
      sender: 'bot',
      text: 'Start with sensor health checks, PLC alarm prioritisation, predictive maintenance thresholds, and a digital checklist. Then add AI summaries for root-cause suggestions and a weekly review dashboard.'
    }
  ];

  chatMessages.innerHTML = defaultMessages
    .map((message) => `
      <div class="message ${message.sender}">
        <span>${message.sender === 'bot' ? 'AI' : 'You'}</span>
        <p>${message.text}</p>
      </div>
    `)
    .join('');
}

function handleChatSubmit(event) {
  event.preventDefault();
  if (!chatInput || !chatMessages) return;

  const value = chatInput.value.trim();
  if (!value) return;

  chatMessages.insertAdjacentHTML(
    'beforeend',
    `
      <div class="message user">
        <span>You</span>
        <p>${value}</p>
      </div>
    `
  );

  const answer = buildAssistantReply(value);
  chatMessages.insertAdjacentHTML(
    'beforeend',
    `
      <div class="message bot">
        <span>AI</span>
        <p>${answer}</p>
      </div>
    `
  );

  chatMessages.scrollTop = chatMessages.scrollHeight;
  chatInput.value = '';
}

function buildAssistantReply(input) {
  const lowered = input.toLowerCase();

  if (lowered.includes('plc') || lowered.includes('ladder') || lowered.includes('safety')) {
    return 'Use a layered PLC sequence: safety interlock checks, conveyor start authorisation, sensor validation, and alarm escalation with time-based fault handling. Add event logs and HMI status indicators for operators.';
  }

  if (lowered.includes('product') || lowered.includes('mvp') || lowered.includes('roadmap')) {
    return 'Define the smallest working version: user needs, pain points, prototype scope, measurable KPIs, delivery timeline, and validation loop. Prioritise reliability and ease of deployment before scaling features.';
  }

  if (lowered.includes('robot') || lowered.includes('packaging')) {
    return 'For packaging automation, evaluate throughput, changeover time, part alignment, guarding, and line balancing. Pair robot motion with line sensors and a clear human override protocol.';
  }

  return 'I can help you turn that into a practical engineering brief: define the objective, constraints, system architecture, test criteria, and decision checkpoints before implementation.';
}

function renderTasks() {
  if (!taskBoard) return;

  taskBoard.innerHTML = tasks
    .map(
      (task) => `
      <div class="task-card">
        <div>
          <h4>${task.title}</h4>
          <p>${task.owner}</p>
        </div>
        <span class="task-status">${task.status}</span>
      </div>
    `
    )
    .join('');

  if (projectCount) {
    projectCount.textContent = String(tasks.length);
  }
}

function handleTaskSubmit(event) {
  event.preventDefault();
  if (!taskForm) return;

  const taskTitle = document.getElementById('taskTitle').value.trim();
  if (!taskTitle) return;

  tasks.unshift({ title: taskTitle, status: 'New', owner: 'You' });
  renderTasks();
  document.getElementById('taskTitle').value = '';
  showToast('Task added to workspace.');
}

function renderProducts() {
  if (!productGrid) return;

  productGrid.innerHTML = products
    .map(
      (product) => `
        <article class="product-card">
          <div class="product-badge">${product.category}</div>
          <h3>${product.name}</h3>
          <div class="product-rating">★★★★★ <span>${product.rating}</span></div>
          <div class="product-footer">
            <strong>$${product.price}</strong>
            <button class="mini-btn" data-product-id="${product.id}">Add to cart</button>
          </div>
        </article>
      `
    )
    .join('');

  document.querySelectorAll('.mini-btn').forEach((button) => {
    button.addEventListener('click', () => {
      const id = Number(button.dataset.productId);
      const product = products.find((entry) => entry.id === id);
      if (!product) return;
      cart.push(product);
      renderCart();
      showToast(`${product.name} added to cart.`);
    });
  });
}

function renderCart() {
  if (!cartItems || !cartCount || !cartTotal) return;

  if (!cart.length) {
    cartItems.innerHTML = '<p class="empty-cart">Your cart is empty.</p>';
    cartCount.textContent = 'Cart: 0';
    cartTotal.textContent = '$0.00';
    return;
  }

  cartItems.innerHTML = cart
    .map(
      (item) => `
        <div class="cart-item">
          <span>${item.name}</span>
          <strong>$${item.price}</strong>
        </div>
      `
    )
    .join('');

  const total = cart.reduce((sum, item) => sum + item.price, 0);
  cartCount.textContent = `Cart: ${cart.length}`;
  cartTotal.textContent = `$${total.toFixed(2)}`;
}

checkoutBtn?.addEventListener('click', () => {
  if (!cart.length) {
    showToast('Add a product before checkout.');
    return;
  }
  cart.length = 0;
  renderCart();
  showToast('Checkout complete. Your order is being processed.');
});

if (ctaForm) {
  ctaForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const button = ctaForm.querySelector('button');
    const input = ctaForm.querySelector('input');

    if (button) {
      button.textContent = 'Joined';
      button.disabled = true;
    }

    if (input) {
      input.value = '';
      input.placeholder = 'Thanks for joining!';
    }

    showToast('You are now part of the CREOVANTA ecosystem.');
  });
}

if (filterButtons.length) {
  filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const selected = button.dataset.filter;

      filterButtons.forEach((btn) => btn.classList.toggle('active', btn === button));
      renderCategories(selected);
    });
  });
}

function initPlatform() {
  renderCategories();
  renderChat();
  renderTasks();
  renderProducts();
  renderCart();
  initNavigation();
  initAuthFlow();

  if (chatForm) {
    chatForm.addEventListener('submit', handleChatSubmit);
  }

  if (taskForm) {
    taskForm.addEventListener('submit', handleTaskSubmit);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPlatform);
} else {
  initPlatform();
}
