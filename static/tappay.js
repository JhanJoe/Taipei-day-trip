function initializeTapPay() {
    // 設置好等等 GetPrime 所需要的金鑰
    TPDirect.setupSDK(151862, 'app_3E0lJM1f7F9nY3IGp3jieuMUZzl9dAJlxbPUUZIko5gGGeVifUm9gjZaI45g', 'sandbox')
        
    // Display ccv field
    let fields = {
        number: {
            // css selector
            element: '#card-number',
            placeholder: '**** **** **** ****'
        },
        expirationDate: {
            // DOM object
            element: document.getElementById('card-expiration-date'),
            placeholder: 'MM / YY'
        },
        ccv: {
            element: '#card-ccv',
            placeholder: 'ccv'
        }
    };
    
    // 把 TapPay 內建輸入卡號的表單給植入到 div 中
    TPDirect.card.setup({
        fields: fields,
        styles: {
            // Style all elements
            'input': {
                'color': 'gray' // 所有輸入欄位的文字顏色
            },
            // Styling ccv field
            'input.ccv': {
                'font-size': '16px'
            },
            // Styling expiration-date field
            'input.expiration-date': {
                'font-size': '16px'
            },
            // Styling card-number field
            'input.card-number': {
                'font-size': '16px'
            },
            // style focus state
            ':focus': {
                'color': 'black'
            },
            // style valid state
            '.valid': {
                'color': 'green'
            },
            // style invalid state
            '.invalid': {
                'color': 'red'
            },
            // Media queries
            // Note that these apply to the iframe, not the root window.
            '@media screen and (max-width: 400px)': {
                'input': {
                    'color': 'orange'
                }
            }
        },
        // 此設定會顯示卡號輸入正確後，會顯示前六後四碼信用卡卡號
        isMaskCreditCardNumber: true,
        maskCreditCardNumberRange: {
            beginIndex: 6,
            endIndex: 11
        }
    });

    // 實作 TPDirect.card.onUpdate，得知目前卡片資訊的輸入狀態 
    TPDirect.card.onUpdate(function (update) {
        // update.canGetPrime === true
        const submitButton = document.getElementById('pay_button');

        // --> you can call TPDirect.card.getPrime()
        if (update.canGetPrime) {
            // Enable submit Button to get prime.
            submitButton.removeAttribute('disabled')
        } else {
            // Disable submit Button to get prime.
            submitButton.setAttribute('disabled', true)
        }
    });


    // Get Prime
    document.getElementById('pay_button').addEventListener('click', async function (event) {
        event.preventDefault();

        await authReady;
        if (!globalUserData) {
            alert("請重新登入");
            window.location.href = '/';
            return;
        }

        const phone = document.getElementById('booking_phone').value;
        const cardNumberStatus = TPDirect.card.getTappayFieldsStatus().status.number;
        const expiryStatus = TPDirect.card.getTappayFieldsStatus().status.expiry;
        const ccvStatus = TPDirect.card.getTappayFieldsStatus().status.ccv;

        if (!phone || cardNumberStatus === 2 || expiryStatus === 2 || ccvStatus === 2) {
            alert("手機、信用卡號、到期日、ccv不得為空或不正確");
            return;
        }

        // 向TapPay發出getPrime的請求  如果result.status==0，表示prime獲取成功
        TPDirect.card.getPrime(async (result) => {
            if (result.status !== 0) {
                return;
            }
            const prime = result.card.prime;


            // 從頁面中取得訂單資料 建立requestBody
            const bookingId = document.getElementById('attraction_id').textContent;;
            const bookingName = document.getElementById('booking_name').textContent;
            const bookingDate = document.getElementById('booking_date').textContent;
            const bookingTime = document.getElementById('booking_time').textContent;
            const bookingCost = parseInt(document.getElementById('booking_cost').textContent.replace('新台幣 ', '').replace(' 元', ''), 10);
            const bookingAddress = document.getElementById('booking_address').textContent;
            const bookingImage = document.getElementById('booking_image').querySelector('img').src;

            const requestBody = {
                prime: prime,
                order: {
                    price: bookingCost,
                    trip: {
                        attraction: {
                            id: bookingId,
                            name: bookingName,
                            address: bookingAddress,
                            image: bookingImage
                        },
                        date: bookingDate,
                        time: bookingTime
                    },
                    contact: {
                        name: document.getElementById('connection_name').value,
                        email: document.getElementById('connection_email').value,
                        phone: phone
                    }
                }
            };

            try {
                const response = await fetch('/api/orders', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify(requestBody)
                });

                const data = await response.json();

                // 檢查回應狀態碼，決定付款成功或失敗
                if (response.ok) {
                    alert('付款成功，訂單編號: ' + data.data.number);
                    setTimeout(() => {
                        window.location.href = `/thankyou?order_number=${data.data.number}`; 
                    }, 1000); 
                } else {
                    alert('付款失敗，暫定訂單編號: ' + data.data.number);
                    setTimeout(() => {
                        window.location.href = `/thankyou?order_number=${data.data.number}`;
                    }, 1000);
                }
            } catch (error) {
                console.error('Error:', error);
                try {
                    const data = await response.json();
                    alert('付款失敗，請稍後再試');
                    setTimeout(() => {
                        window.location.href = `/thankyou?order_number=${data.data.number}`;
                    }, 1000);
                } catch (jsonError) {
                    console.error('Error parsing JSON response:', jsonError);
                    alert('付款失敗，請稍後再試');
                }
            }
        });
    });
};