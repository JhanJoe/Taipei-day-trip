// 顯示登入框的錯誤消息
function showFormMessage(formType, message, isError) {
    const formErrorDiv = document.getElementById(formType === 'login' ? 'login_form_error' : 'register_form_error');
    formErrorDiv.textContent = message;
    formErrorDiv.style.color = isError ? '#FF6347' : '#00970d';
    formErrorDiv.style.textAlign = 'center';
}

// 清空登入輸入框的內容
function clearFormInputs(formType) {
    if (formType === 'login') {
        document.getElementById('login_email').value = '';
        document.getElementById('login_password').value = '';
    } else {
        document.getElementById('register_name').value = '';
        document.getElementById('register_email').value = '';
        document.getElementById('register_password').value = '';
    }
}

// 清空登入框的錯誤消息
function clearFormMessage(formType) {
    const formErrorDiv = document.getElementById(formType === 'login' ? 'login_form_error' : 'register_form_error');
    formErrorDiv.textContent = '';
}

// 以token有無決定登入div動作
document.getElementById('navbar_menu_login').addEventListener('click', function(event) { 
    if (localStorage.getItem('token')) {
        logout();
    } else {
        event.preventDefault(); 
        const modal = document.getElementById('auth_modal'); 

        document.getElementById('login_form').style.display = 'block'; 
        document.getElementById('register_form').style.display = 'none'; 

        modal.style.display = 'block'; 
        setTimeout(() => {
            modal.classList.add('show');
        }, 10); 
    }
});

document.getElementById('close_modal').addEventListener('click', function() { 
    const modal = document.getElementById('auth_modal'); 
    modal.classList.remove('show'); 
    modal.addEventListener('transitionend', function handler() {
        modal.style.display = 'none'; 
        modal.removeEventListener('transitionend', handler); 
    });
});

//點擊登入視窗外部以關閉視窗 
document.getElementById('auth_modal').addEventListener('click', function(event) {
    if (event.target === this) {
        const modal = document.getElementById('auth_modal');
        modal.classList.remove('show');
        modal.addEventListener('transitionend', function handler() {
            modal.style.display = 'none'; 
            modal.removeEventListener('transitionend', handler); 
        });
    }
});

document.getElementById('switch_to_login').addEventListener('click', function() { 
    event.preventDefault(); 
    document.getElementById('register_form').style.display = 'none'; 
    document.getElementById('login_form').style.display = 'block'; 
    clearFormInputs('register'); 
    clearFormMessage('register'); 
});

document.getElementById('switch_to_register').addEventListener('click', function() { 
    event.preventDefault(); 
    document.getElementById('login_form').style.display = 'none'; 
    document.getElementById('register_form').style.display = 'block'; 
    clearFormInputs('login'); 
    clearFormMessage('login'); 

    modal.classList.add('show');
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10); 
});

document.getElementById('register_button').addEventListener('click', function() { 
    const name = document.getElementById('register_name').value; 
    const email = document.getElementById('register_email').value;
    const password = document.getElementById('register_password').value;

    if (!name || !email || !password) {
        showFormMessage('register', '姓名、email、密碼不得為空', true); 
        return;
    }

    register(name, email, password); 
});

document.getElementById('login_button').addEventListener('click', function() { 
    const email = document.getElementById('login_email').value; 
    const password = document.getElementById('login_password').value;

    if (!email || !password) {
        showFormMessage('login', 'email、密碼不得為空', true); 
        return;
    }

    login(email, password); 
});


async function register(name, email, password) {
    const response = await fetch('/api/user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: name, email: email, password: password }) 
    });

    if (response.ok) {
        const data = await response.json();
        showFormMessage('register', '註冊成功', false); 
        
        setTimeout(() => {
            location.reload();
        }, 1000); 

    } else {
        let errorMessage = '您欲註冊的email已存在，無法註冊';
        if (response.status === 500) { 
            errorMessage = '內部伺服器錯誤 (ERROR: 500) 註冊失敗';
        }
        
        showFormMessage('register', errorMessage, true); 
        const errorData = await response.json(); 
        console.error('Registration failed:', errorData.detail); 
    }
}

async function login(email, password) {
    const response = await fetch('/api/user/auth', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email, password: password })
    });

    if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.token);  

        showFormMessage('login', '登入成功，畫面即將跳轉', false);
        const messageElement = document.getElementById('login_form_error');
        let dots = 0;
        const interval = setInterval(() => { 
            dots = (dots + 1) % 4; 
            messageElement.textContent = `登入成功，畫面即將跳轉${'.'.repeat(dots)}`;
        }, 300);

        setTimeout(() => {
            clearInterval(interval); 
            location.reload();
        }, 1200); 

    } else {
        let errorMessage = '輸入帳號、密碼有誤';
        if (response.status === 500) { 
            errorMessage = '內部伺服器錯誤 (ERROR: 500) 登入失敗';
        }
        
        showFormMessage('login', errorMessage, true); 
        const errorData = await response.json(); 
        console.error('Login failed:', errorData.detail); 
    }
}

async function logout() {
    localStorage.removeItem('token');
    location.reload();
}

//將驗證的token資料存進globalUserData變數裡以讓其他函式或js使用
let globalUserData = null; 
let authReady = null; // 存放驗證的 Promise

async function isTokenValid(token) {
    const response = await fetch('/api/user/auth', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        return data; 
    } else {
        return null; 
    }
}

function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));

        return JSON.parse(jsonPayload);
    } catch (e) {
        console.error('Invalid token:', e);
        return null;
    }
}


// 檢查登入狀態並更新按鈕文字
async function updateLoginButton() {
    const token = localStorage.getItem('token');
    const loginButton = document.getElementById('navbar_menu_login');
    if (token) {
        const validUser = await isTokenValid(token);
        if (validUser) {
            globalUserData = parseJwt(token); 
            loginButton.textContent = '登出系統';
            loginButton.removeEventListener('click', clearForm);
            loginButton.addEventListener('click', logout);
        } else {
            localStorage.removeItem('token');
            globalUserData = null;
            loginButton.textContent = '登入/註冊';
            loginButton.removeEventListener('click', logout);
            loginButton.addEventListener('click', clearForm);
        }
    } else {
        globalUserData = null;
        loginButton.textContent = '登入/註冊';
        loginButton.removeEventListener('click', logout);
        loginButton.addEventListener('click', clearForm);
    }
}

function clearForm() {
    clearFormInputs('register');
    clearFormMessage('login');
}


authReady = new Promise((resolve) => { 
    window.addEventListener('load', async () => { 
        await updateLoginButton(); 
        resolve(); 
    });
});



