document.addEventListener('DOMContentLoaded', () => {
    let currentImageIndex = 0; 
    let images = []; 

     function getAttractionIdFromURL() {
        const params = new URLSearchParams(window.location.search);
        return window.location.pathname.split('/').pop();
    }

    async function fetchAttractions(attractionId) { 
        try {
            const response = await fetch(`/api/attraction/${attractionId}`); 
            const data = await response.json(); 
            console.log('Fetched data:', data); 
            renderAttractions(data.data); 
        } catch (error) {
            console.error('Error fetching attractions:', error);
        }
    }

    function renderAttractions(attraction) { 
        images = attraction.images; 

        const imageContainer = document.getElementById('image_container');
        const bigTitle = document.getElementById('attraction_intro_bigtitle');
        const mrt = document.getElementById('attraction_intro_mrt');
        const description = document.getElementById('attraction_intro_description');
        const address = document.getElementById('attraction_intro_address');
        const transport = document.getElementById('attraction_intro_transport');
        const dotsContainer = document.getElementById('dots_container');

        if (images.length > 0) {
            imageContainer.innerHTML = `<img src="${images[0]}" alt="${attraction.name}">`;
            renderDots(images.length); 
        } else {
            imageContainer.innerHTML = 'No image available';
        }

        bigTitle.textContent = attraction.name;
        mrt.textContent = `${attraction.category} at ${attraction.mrt}`;
        description.textContent = attraction.description;
        address.textContent = attraction.address.replace(/\s/g, '');
        transport.textContent = attraction.transport;
    }

    function renderDots(number) {
        const dotsContainer = document.getElementById('dots_container'); 
        dotsContainer.innerHTML = ''; 

        for (let i = 0; i < number; i++) { // 根據圖片數量創建相應數量的圓點
            const dot = document.createElement('span'); 
            dot.classList.add('dot'); 
            if (i === currentImageIndex) { 
                dot.classList.add('active'); 
            }
            dotsContainer.appendChild(dot); 
        }
    }

    function updateDots() {
        const dots = document.querySelectorAll('.dot'); 
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentImageIndex);
        });
    }

    document.getElementById('left_button').addEventListener('click', () => {
        if (currentImageIndex > 0) { 
            currentImageIndex--; 
            document.getElementById('image_container').innerHTML = `<img src="${images[currentImageIndex]}" alt="Image">`; // 更新圖片容器，顯示前一張圖片
            updateDots(); 
        }
    });

    document.getElementById('right_button').addEventListener('click', () => {
        if (currentImageIndex < images.length - 1) {  
            currentImageIndex++;
            document.getElementById('image_container').innerHTML = `<img src="${images[currentImageIndex]}" alt="Image">`;
            updateDots(); 
        }
    });

    const costContainer = document.getElementById('cost');
    costContainer.textContent = '新台幣 2000 元';

    // 時間單選選單
    document.querySelectorAll('input[name="day_time"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const costContainer = document.getElementById('cost');
            if (this.value === '上半天') {
                costContainer.textContent = '新台幣 2000 元';
            } else if (this.value === '下半天') {
                costContainer.textContent = '新台幣 2500 元';
            }
        });
    });
    
    const attractionId = getAttractionIdFromURL();
    if (attractionId) {
        fetchAttractions(attractionId);
    } else {
        console.error('No attraction id found in URL');
    }

});