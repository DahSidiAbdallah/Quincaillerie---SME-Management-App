/**
 * Customer Management Module
 * Handles all customer-related frontend operations
 */

// Customer management functions
function customerManager() {
    return {
        customers: [],
        isLoading: true,
        error: null,
        searchTerm: '',
        showCustomerModal: false,
        showConfirmDeleteModal: false,
        editMode: false,
        selectedCustomerId: null,
        
        newCustomer: {
            name: '',
            phone: '',
            email: '',
            address: ''
        },
        
        init() {
            this.loadCustomers();
        },
        
        loadCustomers() {
            this.isLoading = true;
            fetch('/api/customers')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.customers = data.customers || [];
                        this.error = null;
                    } else {
                        this.error = data.error || 'Erreur lors du chargement des clients';
                    }
                    this.isLoading = false;
                })
                .catch(error => {
                    console.error('Error loading customers:', error);
                    this.error = 'Erreur de connexion au serveur';
                    this.isLoading = false;
                });
        },
        
        get filteredCustomers() {
            return this.customers.filter(customer => 
                !this.searchTerm || 
                customer.name.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
                (customer.phone && customer.phone.includes(this.searchTerm))
            );
        },
        
        clearForm() {
            this.newCustomer = {
                name: '',
                phone: '',
                email: '',
                address: ''
            };
            this.editMode = false;
            this.selectedCustomerId = null;
        },
        
        showAddCustomerModal() {
            this.clearForm();
            this.showCustomerModal = true;
        },
        
        showEditCustomerModal(customerId) {
            this.isLoading = true;
            fetch(`/api/customers/${customerId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const customer = data.customer;
                        this.newCustomer = {
                            name: customer.name || '',
                            phone: customer.phone || '',
                            email: customer.email || '',
                            address: customer.address || ''
                        };
                        this.editMode = true;
                        this.selectedCustomerId = customerId;
                        this.showCustomerModal = true;
                    } else {
                        alert('Erreur lors du chargement des données client: ' + (data.error || 'Client non trouvé'));
                    }
                    this.isLoading = false;
                })
                .catch(error => {
                    console.error('Error loading customer details:', error);
                    alert('Erreur de connexion au serveur');
                    this.isLoading = false;
                });
        },
        
        saveCustomer() {
            if (!this.newCustomer.name) {
                alert('Le nom du client est requis');
                return;
            }
            
            // Basic email validation
            if (this.newCustomer.email && !this.newCustomer.email.includes('@')) {
                alert('Format d\'email invalide');
                return;
            }
            
            this.isLoading = true;
            
            if (this.editMode) {
                // Update existing customer
                fetch(`/api/customers/${this.selectedCustomerId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.newCustomer)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.loadCustomers();
                        this.showCustomerModal = false;
                        this.clearForm();
                        alert('Client mis à jour avec succès');
                    } else {
                        alert('Erreur: ' + (data.error || 'Échec de la mise à jour'));
                    }
                    this.isLoading = false;
                })
                .catch(error => {
                    console.error('Error updating customer:', error);
                    alert('Erreur de connexion au serveur');
                    this.isLoading = false;
                });
            } else {
                // Create new customer
                fetch('/api/customers', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.newCustomer)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.loadCustomers();
                        this.showCustomerModal = false;
                        this.clearForm();
                        alert('Client ajouté avec succès');
                    } else {
                        alert('Erreur: ' + (data.error || 'Échec de l\'ajout'));
                    }
                    this.isLoading = false;
                })
                .catch(error => {
                    console.error('Error creating customer:', error);
                    alert('Erreur de connexion au serveur');
                    this.isLoading = false;
                });
            }
        },
        
        confirmDelete(customerId) {
            this.selectedCustomerId = customerId;
            this.showConfirmDeleteModal = true;
        },
        
        deleteCustomer() {
            if (!this.selectedCustomerId) return;
            
            this.isLoading = true;
            fetch(`/api/customers/${this.selectedCustomerId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.loadCustomers();
                    alert('Client supprimé avec succès');
                } else {
                    alert('Erreur: ' + (data.error || 'Échec de la suppression'));
                }
                this.showConfirmDeleteModal = false;
                this.selectedCustomerId = null;
                this.isLoading = false;
            })
            .catch(error => {
                console.error('Error deleting customer:', error);
                alert('Erreur de connexion au serveur');
                this.showConfirmDeleteModal = false;
                this.isLoading = false;
            });
        }
    };
}
