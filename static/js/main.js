/* ---
    Midnight Indigo - main.js v1.0
    Baseado no Smashed Potatoes v2.4, mas limpo e otimizado
    para a estrutura do e-commerce.
--- */

/**
 * Função principal que inicializa todos os scripts
 * após o carregamento do DOM.
 */
 document.addEventListener("DOMContentLoaded", () => {
    
    // Inicializa o dropdown de usuário na navbar
    initUserDropdown();

    // Inicializa o efeito de fade-in para elementos com a classe .fade-in
    initFadeInObserver();

    // Inicializa os contadores de caracteres para inputs e textareas
    initCharCounters();

    // Inicializa o botão "Voltar ao Topo"
    initScrollTopButton();

}); // <-- FIM DO "DOMContentLoaded"


/**
 * 1. LÓGICA DO DROPDOWN DE USUÁRIO
 * Encontra o dropdown pelo ID e adiciona os eventos de clique
 * para abrir/fechar o menu.
 */
function initUserDropdown() {
    const dropdown = document.getElementById('user-dropdown');
    
    if (dropdown) {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');

        toggle.addEventListener('click', (e) => {
            // Impede que o clique no 'toggle' feche o menu imediatamente
            e.stopPropagation(); 
            menu.classList.toggle('active');
        });

        // Evento global para fechar o dropdown se clicar fora dele
        window.addEventListener('click', (e) => {
            if (menu.classList.contains('active') && !dropdown.contains(e.target)) {
                menu.classList.remove('active');
            }
        });
    }
}


/**
 * 2. LÓGICA DE FADE-IN (com IntersectionObserver)
 * Observa elementos com a classe .fade-in e adiciona
 * a classe .is-visible quando eles entram na tela.
 */
function initFadeInObserver() {
    const elementsToFade = document.querySelectorAll('.fade-in');
    
    // Se não houver elementos, não faz nada
    if (elementsToFade.length === 0) return;

    // Configurações do Observer
    const observerOptions = {
        root: null,       // Viewport
        rootMargin: '0px',
        threshold: 0.1    // 10% do item precisa estar visível
    };

    // O que fazer quando um item observado entra na tela
    const observerCallback = (entries, observer) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                // Para de observar o item após a animação
                observer.unobserve(entry.target); 
            }
        });
    };

    // Cria e inicia o observer
    const observer = new IntersectionObserver(observerCallback, observerOptions);
    elementsToFade.forEach(element => {
        observer.observe(element);
    });
}


/**
 * 3. LÓGICA DO CONTADOR DE CARACTERES
 * Encontra todos os inputs/textareas com 'maxlength' e
 * atualiza o contador de caracteres associado a eles.
 */
function initCharCounters() {
    const inputsWithMaxlength = document.querySelectorAll('input[maxlength], textarea[maxlength]');

    inputsWithMaxlength.forEach(input => {
        // Encontra o 'input-wrapper' mais próximo
        const wrapper = input.closest('.input-wrapper');
        if (!wrapper) return;
        
        // Encontra o contador dentro do wrapper
        let counter = wrapper.querySelector('.char-counter');

        // (Lógica do seu projeto antigo) Se não achar, procura como irmão
        if (!counter && wrapper.nextElementSibling && wrapper.nextElementSibling.classList.contains('char-counter')) {
            counter = wrapper.nextElementSibling;
        }
        
        // Se não houver contador, não faz nada
        if (!counter) return;

        const maxLen = input.getAttribute('maxlength');
        
        function updateCounter() {
            const currentLen = input.value.length;
            counter.textContent = `${currentLen} / ${maxLen}`;
            // Adiciona classe 'danger' se estiver perto do limite
            counter.classList.toggle('danger', currentLen >= maxLen);
        }

        input.addEventListener('input', updateCounter);
        // Atualiza o contador ao carregar a página (para o form 'edit')
        updateCounter();
    });
}


/**
 * 4. LÓGICA DO BOTÃO "VOLTAR AO TOPO"
 * Mostra o botão quando o usuário rola a página para baixo
 * e rola suavemente para o topo ao ser clicado.
 */
function initScrollTopButton() {
    const scrollTopBtn = document.getElementById('scrollTopBtn');
    
    if (scrollTopBtn) {
        // Mostrar/Esconder o botão
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                scrollTopBtn.classList.add('visible');
            } else {
                scrollTopBtn.classList.remove('visible');
            }
        });

        // Ação de clique
        scrollTopBtn.addEventListener('click', (e) => {
            e.preventDefault(); // Impede que o '#' vá para a URL
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}