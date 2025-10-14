// Fixed JavaScript for the template
document.addEventListener('DOMContentLoaded', function() {
    // Add click listeners to marketplace buttons
    function redirectToCheckout(e) {
        let package = e.getAttribute("name");
        // Check if user is authenticated
        if (!'{{ user.is_authenticated }}' || '{{ user.is_authenticated }}' === 'False') {
            alert('Please log in to continue with checkout.');
            return;
        }

        // Check if user has email
        let userEmail = '{{ user.email }}';
        if (!userEmail || userEmail.trim() === '') {
            // For superuser or accounts without email, prompt for email
            const email = prompt('Please enter your email address for checkout:');
            if (!email || email.trim() === '') {
                alert('Email address is required for checkout.');
                return;
            }
            userEmail = email.trim();
        }

        // Show loading state
        const buttons = document.querySelectorAll('.market');
        buttons.forEach(btn => {
            btn.disabled = true;
        });

        fetch('/create-checkout-session/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify({
                email: userEmail,
                product: package
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(`Server error: ${errorData.error || 'Unknown error'}`);
                });
            }
            return response.json();
        })
        .then(session => {
            if (session.url) {
                window.location.href = session.url;
            } else {
                throw new Error('No checkout URL received from server');
            }
        })
        .catch(error => {
            // Reset button states
            buttons.forEach(btn => {
                btn.disabled = false;
            });
            alert(`Checkout Error: ${error.message || 'Unknown error occurred'}`);
        });
    }

    function proceedToCancel() {
        // Redirect to Stripe billing portal
        window.location.href = 'https://billing.stripe.com/p/login/test_5kQ28r3YY9IE7Ofa6W3ZK01';
    }

    function handleSeamlessVpnAccess(serverDns = null) {
        // Check if we already have a JWT token in sessionStorage
        const existingToken = sessionStorage.getItem('portbro_jwt_token');
        
        if (existingToken) {
            // Redirect to VPN node (use server parameter or default)
            const vpnNodeUrl = serverDns ? `http://${serverDns}` : 'https://vpn.portbro.com';
            const redirectUrl = `${vpnNodeUrl}/auth/callback/?token=${existingToken}&redirect_url=/dashboard/`;
            
            // Open in new tab for better UX
            window.open(redirectUrl, '_blank');
            
            return;
        }
        
        // FIXED: Use the correct endpoint
        fetch('/auth/vpn/token/', {
            method: 'POST',  // Changed to POST
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                force_refresh: false
            })
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    throw new Error('Authentication required. Please log in again.');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.access_token) {  // Changed from data.token to data.access_token
                // Store token in sessionStorage for the VPN node to use
                sessionStorage.setItem('portbro_jwt_token', data.access_token);
                sessionStorage.setItem('portbro_token_expires', data.expires_in);
                
                // Redirect to VPN node (use server parameter or default)
                const vpnNodeUrl = serverDns ? `http://${serverDns}` : 'https://vpn.portbro.com';
                const redirectUrl = `${vpnNodeUrl}/auth/callback/?token=${data.access_token}&redirect_url=/dashboard/`;
                
                // Open in new tab for better UX
                window.open(redirectUrl, '_blank');
                
            } else {
                throw new Error(data.error || 'Failed to get JWT token');
            }
        })
        .catch(error => {
            console.error('VPN authentication error:', error);
            alert(`Failed to connect to VPN node: ${error.message}`);
        });
    }

    // Utility function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        
        return cookieValue;
    }

    // Make functions globally available
    window.proceedToCancel = proceedToCancel;
    window.handleSeamlessVpnAccess = handleSeamlessVpnAccess;
    window.redirectToCheckout = redirectToCheckout;
});
