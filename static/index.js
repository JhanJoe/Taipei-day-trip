document.addEventListener('DOMContentLoaded', () => {
    let nextPage = 0; 
    let isLoading = false; 
    let keyword = ''; 

    fetchMRTStations();
    fetchAttractions(nextPage, keyword);

    const observer = new IntersectionObserver(handleIntersection, {
        root: null, 
        rootMargin: '0px', 
        threshold: 1.0 
    });

    observer.observe(document.querySelector('.footer'));

    document.getElementById('search_button').addEventListener('click', () => {
        keyword = document.getElementById('search').value.trim();
        if (keyword) {
            performSearch();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') { 
            keyword = document.getElementById('search').value.trim();
            if (keyword) { 
                performSearch();
            }
        }
    });

    function performSearch() {
        nextPage = 0; 
        document.getElementById('attractions').innerHTML = ''; 

        observer.unobserve(document.querySelector('.footer'));
        fetchAttractions(nextPage, keyword); 
    }

    function handleIntersection(entries) {
        entries.forEach(entry => {            
            if (entry.isIntersecting && !isLoading && nextPage !== null) {
                fetchAttractions(nextPage, keyword); 
            }
        });
    }

    async function fetchAttractions(page, keyword) {
        isLoading = true; 
        try {
            let url = `/api/attractions?page=${page}`;
            if (keyword) { 
                url += `&keyword=${encodeURIComponent(keyword)}`;
            }

            const response = await fetch(url); 
            const data = await response.json(); 
            renderAttractions(data.data); 

            if (data.nextPage !== null) { 
                nextPage = data.nextPage;
                observer.observe(document.querySelector('.footer'));
            } else { 
                nextPage = null;
                observer.unobserve(document.querySelector('.footer'));
            }
        } catch (error) {
            console.error('Error fetching attractions:', error);
        } finally {
            isLoading = false; 
        }
    }

    function renderAttractions(attractions) {
        const container = document.getElementById('attractions');

        attractions.forEach(attraction => {
            const attractionDiv = document.createElement('div');
            attractionDiv.className = 'attraction'; 
            attractionDiv.setAttribute('data-id', attraction.id);

            const imageUrl = attraction.images.length > 0 ? attraction.images[0] : '';
            console.log('Image URL:', imageUrl); 

            const attractionHTML = `
                <div class="attraction_image" style="background-image: url(${attraction.images[0]});">
                    <div class="attraction_name_overlay">
                        <span class="attraction_name_overlay_text">${attraction.name}</span>
                    </div>
                </div>
                <div class="attraction_info">
                    <span class="attraction_mrt">${attraction.mrt}</span>
                    <span class="attraction_category">${attraction.category}</span>
                </div>
            `;

            attractionDiv.innerHTML = attractionHTML;
            container.appendChild(attractionDiv);
            
            attractionDiv.addEventListener('click', () => {
                const attractionId = attractionDiv.getAttribute('data-id');
                window.location.href = `/attraction/${attractionId}`;
            });
        });
    }

    async function fetchMRTStations() {
        try {
            const response = await fetch('/api/mrts');
            const data = await response.json();
            renderMRTStations(data.data);
        } catch (error) {
            console.error('Error fetching MRT stations:', error);
        }
    }

    function renderMRTStations(stations) {
        const container = document.getElementById('mrt_list_stations');
        stations.forEach(station => {
            const stationDiv = document.createElement('div');
            stationDiv.className = 'mrt_station';
            stationDiv.innerText = station;

            stationDiv.addEventListener('click', () => {
                document.getElementById('search').value = station;
                keyword = station;
                nextPage = 0;
                document.getElementById('attractions').innerHTML = '';
                observer.unobserve(document.querySelector('.footer'));
                fetchAttractions(nextPage, keyword);
            });
            container.appendChild(stationDiv);
        });

        document.getElementById('mrt_list_left').addEventListener('click', () => {
            container.scrollBy({ left: -0.8 * container.clientWidth, behavior: 'smooth' });
        });

        document.getElementById('mrt_list_right').addEventListener('click', () => {
            container.scrollBy({ left: 0.8 * container.clientWidth, behavior: 'smooth' });
        });
    }
});