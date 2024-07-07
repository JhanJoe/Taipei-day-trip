document.addEventListener('DOMContentLoaded', async () => {
    await authReady; 

    if (!globalUserData) {
        window.location.href = '/';
    } else {
        const token = localStorage.getItem('token');
        document.getElementById('booking_welcome').textContent = `您好，${globalUserData.name}，待預訂的行程如下：`;
        await fetchBookingInfo(token);
        const bookingData = document.querySelector('.booking_yes').style.display !== 'none';
        // 有預定資料才引入tappay
        if (bookingData) {
            initializeTapPay();
        }
    }
});

async function fetchBookingInfo(token) {
    try {
        const response = await fetch('/api/booking', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/';
            return;
        }
  
        if (response.status === 500) {
            displayBookingInfo(null);
            updateFooter(null);
            return;
        }

        if (response.ok) {
            const data = await response.json();
            displayBookingInfo(data.data);
            updateFooter(data.data);
            calculateTotalCost();
        } else {
            displayBookingInfo(null);
            updateFooter(null);
        }
    } catch (error) {
        console.error('Error fetching booking info:', error);
        displayBookingInfo(null);
        updateFooter(null);
    }
}

function displayBookingInfo(booking) {
    const bookingNone = document.getElementById('booking_none');
    const bookingYes = document.querySelector('.booking_yes');

    if (!booking) {
        bookingNone.style.display = 'block';
        bookingYes.style.display = 'none';
        return;
    }
    bookingNone.style.display = 'none';
    bookingYes.style.display = 'block';

    const bookingName = document.getElementById('booking_name');
    bookingName.textContent = booking.attraction.name;
    bookingName.style.cursor = 'pointer';
    bookingName.onclick = () => {
        window.location.href = `/attraction/${booking.attraction.id}`;
    };

    document.getElementById('attraction_id').textContent = booking.attraction.id;   
    document.getElementById('booking_date').textContent = booking.date;
    document.getElementById('booking_time').textContent = booking.time;
    document.getElementById('booking_cost').textContent = `新台幣 ${booking.price} 元`;
    document.getElementById('booking_address').textContent = booking.attraction.address;
    document.getElementById('booking_cost').classList.add('booking_price'); 

    const bookingImage = document.getElementById('booking_image');
    if (booking.attraction.image) {
        bookingImage.innerHTML = `<img src="${booking.attraction.image}" alt="${booking.attraction.name}" />`;
        bookingImage.style.cursor = 'pointer';
        bookingImage.onclick = () => {
            window.location.href = `/attraction/${booking.attraction.id}`;
        };
    }

    document.getElementById('connection_name').value = globalUserData.name;
    document.getElementById('connection_email').value = globalUserData.sub;
}

function updateFooter(data) {
    const footer = document.querySelector('.footer');
    if (!data || data.length === 0) {
        footer.classList.add('expanded');
    } else {
        footer.classList.remove('expanded');
    }
}

function calculateTotalCost() {
    const prices = document.querySelectorAll('.booking_price');
    let totalCost = 0;
    prices.forEach(priceElement => {
        const priceText = priceElement.textContent.replace('新台幣 ', '').replace(' 元', '');
        const price = parseInt(priceText, 10);
        if (!isNaN(price)) {
            totalCost += price;
        }
    });
    document.getElementById('total_cost').textContent = `新台幣 ${totalCost} 元`;
}