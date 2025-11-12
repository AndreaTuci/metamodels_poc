// Auth Manager centralizzato per gestire autenticazione e token scaduti

class AuthManager {
    static TOKEN_KEY = 'authToken';
    static USER_INFO_KEY = 'userInfo';
    static TOKEN_TIMESTAMP_KEY = 'authTokenTimestamp';
    static TOKEN_EXPIRY_HOURS = 24; // Durata token stimata (configurabile)

    /**
     * Verifica se l'utente è autenticato e se il token è ancora valido
     */
    static isAuthenticated() {
        const token = localStorage.getItem(this.TOKEN_KEY);
        if (!token) {
            return false;
        }

        // Verifica se il token è scaduto (controllo locale)
        if (this.isTokenExpired()) {
            this.clearAuth();
            return false;
        }

        return true;
    }

    /**
     * Verifica se il token è scaduto localmente
     */
    static isTokenExpired() {
        const timestamp = localStorage.getItem(this.TOKEN_TIMESTAMP_KEY);
        if (!timestamp) {
            return true; // Se non abbiamo timestamp, consideriamo scaduto
        }

        const tokenAge = Date.now() - parseInt(timestamp);
        const maxAge = this.TOKEN_EXPIRY_HOURS * 60 * 60 * 1000; // Converti in millisecondi
        return tokenAge > maxAge;
    }

    /**
     * Salva i dati di autenticazione
     */
    static setAuth(token, userInfo) {
        localStorage.setItem(this.TOKEN_KEY, token);
        localStorage.setItem(this.USER_INFO_KEY, JSON.stringify(userInfo));
        localStorage.setItem(this.TOKEN_TIMESTAMP_KEY, Date.now().toString());
    }

    /**
     * Pulisce tutti i dati di autenticazione
     */
    static clearAuth() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_INFO_KEY);
        localStorage.removeItem(this.TOKEN_TIMESTAMP_KEY);
    }

    /**
     * Ottiene il token corrente
     */
    static getToken() {
        if (!this.isAuthenticated()) {
            return null;
        }
        return localStorage.getItem(this.TOKEN_KEY);
    }

    /**
     * Ottiene le info utente
     */
    static getUserInfo() {
        const userInfo = localStorage.getItem(this.USER_INFO_KEY);
        return userInfo ? JSON.parse(userInfo) : null;
    }

    /**
     * Effettua una richiesta autenticata con gestione automatica dei token scaduti
     */
    static async makeAuthenticatedRequest(url, options = {}) {
        // Verifica autenticazione prima della richiesta
        if (!this.isAuthenticated()) {
            this.redirectToLogin();
            throw new Error('Non autenticato');
        }

        const token = this.getToken();
        
        // Prepara gli headers
        const defaultHeaders = {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`
        };

        // Se è FormData, non impostare Content-Type (il browser lo gestirà)
        if (options.body instanceof FormData) {
            delete defaultHeaders['Content-Type'];
        }

        const finalOptions = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, finalOptions);

            // Gestione token scaduto o non autorizzato
            if (response.status === 401 || response.status === 403) {
                console.log('Token scaduto o non autorizzato, effettuo logout...');
                await this.handleTokenExpired();
                throw new Error('Token scaduto');
            }

            return response;
        } catch (error) {
            // Se è un errore di rete, non fare logout automatico
            if (error.message === 'Token scaduto') {
                throw error;
            }
            
            // Per altri errori, lasciali passare
            throw error;
        }
    }

    /**
     * Gestisce il token scaduto
     */
    static async handleTokenExpired() {
        console.log('Gestisco token scaduto...');
        
        try {
            // Prova a fare logout dal backend se possibile
            const token = localStorage.getItem(this.TOKEN_KEY);
            if (token) {
                await fetch('http://localhost:8000/auth/logout/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Token ${token}`,
                        'Content-Type': 'application/json'
                    }
                }).catch(() => {}); // Ignora errori del logout
            }
        } catch (error) {
            // Ignora errori del logout - procediamo comunque con la pulizia locale
            console.log('Errore durante logout dal backend (ignorato):', error);
        }

        // Pulisci tutto
        this.clearAuth();
        
        // Mostra notifica all'utente
        this.showExpiredMessage();
        
        // Redirect dopo un piccolo delay
        setTimeout(() => {
            this.redirectToLogin();
        }, 2000);
    }

    /**
     * Mostra messaggio di sessione scaduta
     */
    static showExpiredMessage() {
        // Crea un toast di notifica
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f44336;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 300px;
            animation: slideIn 0.3s ease-out;
        `;
        
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 20px;">⚠️</span>
                <div>
                    <div style="font-weight: 600; margin-bottom: 4px;">Sessione Scaduta</div>
                    <div style="font-size: 14px; opacity: 0.9;">Verrai reindirizzato al login...</div>
                </div>
            </div>
        `;

        // Aggiungi animazione
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(toast);

        // Rimuovi dopo 3 secondi
        setTimeout(() => {
            toast.remove();
            style.remove();
        }, 3000);
    }

    /**
     * Redirect al login
     */
    static redirectToLogin() {
        window.location.href = '/login';
    }

    /**
     * Verifica autenticazione per pagine protette
     */
    static requireAuth() {
        if (!this.isAuthenticated()) {
            this.redirectToLogin();
            return false;
        }
        return true;
    }

    /**
     * Effettua logout manuale
     */
    static async logout() {
        try {
            const token = this.getToken();
            if (token) {
                await fetch('http://localhost:8000/auth/logout/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Token ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
            }
        } catch (error) {
            console.log('Errore durante logout (ignorato):', error);
        }

        this.clearAuth();
        this.redirectToLogin();
    }
}

// Esporta come oggetto globale per compatibilità con gli script esistenti
window.AuthManager = AuthManager;

// Esporta anche come modulo
export default AuthManager;