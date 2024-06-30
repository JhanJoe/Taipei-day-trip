document.addEventListener('DOMContentLoaded', async () => {
    await authReady; 
    const navbarReservationButton = document.getElementById('navbar_menu_reservation');
    const bookingButton = document.getElementById('booking_button');
    const bookingForm = document.getElementById('booking_form');
    const deleteButton = document.getElementById('delete_button');

    if (navbarReservationButton) {
        // 為 "預定行程" 按鈕添加點擊事件監聽器
        navbarReservationButton.addEventListener('click', async () => {
            await handleReservationClick();
        });
    }

    if (bookingButton) {
        bookingForm.addEventListener('submit', async (event) => {
            event.preventDefault(); 
            await handleBookingClick();
        });
    }

    if (deleteButton) {
        deleteButton.addEventListener('click', handleDeleteClick);
    }

    // navbar的預定行程按鈕
    async function handleReservationClick() {
        if (globalUserData) {
            window.location.href = '/booking';
        } else {
            openLoginModal();
        }
    }

    //attractional.html的開始預約行程按鈕
    async function handleBookingClick() {
        if (globalUserData) {
            const token = localStorage.getItem('token');
            await createBooking(token);
        } else {
            openLoginModal();
        }
    }

    //booking.html的刪除行程按鈕
    async function handleDeleteClick() {
        if (confirm('確定刪除此預定行程？')) {
            if (globalUserData) {
                const token = localStorage.getItem('token');
                await deleteBooking(token);
            } else {
                redirectToHome();
            }
        }
    }

    async function createBooking(token) {
        const attractionId = getAttractionIdFromURL();
        const date = document.getElementById('date').value;
        const time = document.querySelector('input[name="day_time"]:checked').value;
        const price = document.getElementById('attraction_cost').textContent.match(/\d+/)[0];

        const requestBody = {
            attractionId: parseInt(attractionId),
            date: date,
            time: time,
            price: parseInt(price)
        };

        const response = await fetch('/api/booking', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(requestBody)
        });

        if (response.ok) {
            window.location.href = '/booking';
        } else {
            console.error('Failed to create booking', await response.json());
        }
    }

    //顯示登入視窗
    function openLoginModal() {
        const modal = document.getElementById('auth_modal');
        document.getElementById('login_form').style.display = 'block';
        document.getElementById('register_form').style.display = 'none';
        modal.style.display = 'block';
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }

    //booking.html的刪除行程按鈕
    async function deleteBooking(token) {
        const response = await fetch('/api/booking', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            window.location.href = '/booking';
        } else {
            console.error('Failed to delete booking', await response.json());
        }
    }

    function redirectToHome() {
        localStorage.removeItem('token');
        window.location.href = '/';
    }

    function getAttractionIdFromURL() {
        return window.location.pathname.split('/').pop();
    }
});

