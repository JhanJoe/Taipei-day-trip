document.addEventListener("DOMContentLoaded", async function () {
    await authReady;
    if (!globalUserData) {
        window.location.href = '/';
        return;
    }

    const params = new URLSearchParams(window.location.search);
    const orderNumber = params.get('order_number');
    
    if (!orderNumber) {
        document.getElementById('thank_welcome').textContent= "無效的訂單編號"
        return;
    }

    try {
        const response = await fetch(`/api/order/${orderNumber}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!response.ok) {
            throw new Error('無法取得訂單資訊');
        }

        const result = await response.json();
        const orderData = result.data;

        document.getElementById('thank_welcome').textContent = `您好，${globalUserData.name}，您已付款的行程如下：`;

        document.getElementById('thank_order_number').textContent = `訂單編號：${orderData.number}`;
        document.getElementById('thank_attraction_name').textContent = `景點名稱：${orderData.trip.attraction.name}`;
        document.getElementById('thank_order_address').textContent = `行程地址：${orderData.trip.attraction.address}`;
        document.getElementById('thank_order_date').textContent = `行程日期：${orderData.trip.date}`;
        document.getElementById('thank_order_time').textContent = `行程時間：${orderData.trip.time}`;
    

        const thankImage = document.getElementById('thank_image');
        const img = document.createElement('img');
        img.src = orderData.trip.attraction.image;
        thankImage.appendChild(img);

    } catch (error) {
        console.error('Error:', error);
        alert('無法取得訂單資訊，請稍後再試');
    }
});
