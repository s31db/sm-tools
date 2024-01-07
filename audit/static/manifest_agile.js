const apiUrl = 'manifest_agile_fr.json';
const postUrl = 'save_results';

// Fonction pour charger les données depuis le service REST
async function loadData(apiUrl, tableBodyId, key) {
    const response = await fetch(apiUrl);
    const data = await response.json();
    const tableBody = document.getElementById(tableBodyId);

    // Parcours des données JSON et création des lignes du tableau
    data[key].forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="data-cell">${item}</td>
            <td class="emoji-cell" data-emoji="😠"></td>
            <td class="emoji-cell" data-emoji="😟"></td>
            <td class="emoji-cell" data-emoji="😕"></td>
            <td class="emoji-cell" data-emoji="😐"></td>
            <td class="emoji-cell" data-emoji="😊"></td>
            <td class="emoji-cell" data-emoji="😄"></td>
            <td class="emoji-cell" data-emoji="😍"></td>
        `;
        tableBody.appendChild(row);
    });

    // Ajout d'un gestionnaire d'événements de clic aux cellules d'emoji
    const emojiCells = tableBody.querySelectorAll('.emoji-cell');
    emojiCells.forEach(cell => {
        cell.addEventListener('click', handleEmojiClick);
    });
}

// Gestionnaire d'événements de clic pour les cellules d'emoji
function handleEmojiClick(event) {
    const selectedEmoji = event.currentTarget.getAttribute('data-emoji');
    const currentContent = event.currentTarget.textContent;

    if (currentContent === selectedEmoji) {
        // Si le smiley est déjà sélectionné, annuler l'évaluation
        event.currentTarget.textContent = '';
    } else {
        // Sinon, définir le nouveau smiley
        event.currentTarget.textContent = selectedEmoji;
    }
}

// Fonction pour gérer la soumission du formulaire
function submitForm() {
    const valuesEmojiData = getEmojiDataWithLabels('values-table-body');
    const principlesEmojiData = getEmojiDataWithLabels('principles-table-body');

    // Créez un objet avec les données que vous souhaitez envoyer
    const formData = {
        user: document.getElementById('user').value,
        values: valuesEmojiData,
        principles: principlesEmojiData
    };

    // Envoiez la requête POST avec les données du formulaire
    fetch(postUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        //console.log('Réponse du serveur:', data);
        //displayResults(data);
        const message = document.getElementById('message');
        message.style.display = 'block';
        setTimeout(() => {message.style.display = 'none';}, 1500);
    })
    .catch(error => {
        console.error('Erreur lors de la soumission du formulaire:', error);
        alert('Une erreur s\'est produite lors de la soumission du formulaire.');
    });
}

// Fonction pour obtenir les données des emoji d'un tableau
function getEmojiData(tableBodyId) {
    const emojiCells = document.getElementById(tableBodyId).querySelectorAll('.emoji-cell');
    const emojiData = [];

    emojiCells.forEach(cell => {
        const emojiValue = cell.textContent.trim();
        emojiData.push(emojiValue);
    });

    return emojiData;
}

// Fonction pour obtenir les données des emoji d'un tableau avec les libellés
function getEmojiDataWithLabels(tableBodyId) {
    const rows = document.getElementById(tableBodyId).querySelectorAll('tr');
    const emojiDataWithLabels = [];

    rows.forEach((row, rowIndex) => {
        const cells = row.querySelectorAll('.emoji-cell');
        const emojis = [];

        cells.forEach((cell, columnIndex) => {
            const emojiValue = cell.textContent.trim();
            if (emojiValue !== '') {
                emojis.push({
                column: columnIndex + 1, // Ajout du numéro de colonne
                emoji: emojiValue
            });
            }
        });

        if (emojis.length > 0) {
            const rowData = {
                label: row.querySelector('td').textContent.trim(),
                row: rowIndex + 1,
                emojis: emojis
            };
            emojiDataWithLabels.push(rowData);
        }
    });

    return emojiDataWithLabels;
}

// Fonction pour afficher les résultats dans le document HTML
function displayResults(results) {
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '<h2>Résultats</h2>';

    results.values.forEach(value => {
        resultsContainer.innerHTML += `<p>${value.label}: ${value.emojis.join(', ')}</p>`;
    });

    results.principles.forEach(principle => {
        resultsContainer.innerHTML += `<p>${principle.label}: ${principle.emojis.join(', ')}</p>`;
    });
}

// Appel de la fonction pour charger les données au chargement de la page
window.onload = function () {
    loadData(apiUrl, 'values-table-body', 'valeurs');
    loadData(apiUrl, 'principles-table-body', 'principes');
};