const apiUrl = 'audit_fr.json';
const postUrl = 'save_results';
const audit_ids = ['squad_health_check', 'kanban', 'Scrum_values', 'Scrum_piliers', 'Scrum'];

// Fonction pour charger les données depuis le service REST
async function loadData(apiUrl, key) {
    const response = await fetch(apiUrl);
    const data = await response.json();
    const divBody = document.getElementById('audit-container');
    const title = document.createElement('h2');
    divBody.appendChild(title);
    title.textContent = data[key].label;
    const table = document.createElement('table');
    table.innerHTML = `<thead>
        <tr>
            <th class="data-cell">`+data[key].describer+`</th>
            <th>😠</th>
            <th>😟</th>
            <th>😕</th>
            <th>😐</th>
            <th>😊</th>
            <th>😄</th>
            <th>😍</th>
        </tr>
    </thead>`;
    const tableBody = document.createElement('tbody');
    tableBody.id = key;
    table.appendChild(tableBody);

    // Parcours des données JSON et création des lignes du tableau
    data[key].values.forEach(item => {
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
    divBody.appendChild(table);

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

    // Créez un objet avec les données que vous souhaitez envoyer
    const formData = {
        user: document.getElementById('user').value
    };
    audit_ids.forEach(list_id => {
        formData[list_id] = getEmojiDataWithLabels(list_id);
    })

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
        const message = document.getElementById('message');
        message.style.display = 'block';
        setTimeout(() => {message.style.display = 'none';}, 1500);
    })
    .catch(error => {
        console.error('Erreur lors de la soumission du formulaire:', error);
        alert('Une erreur s\'est produite lors de la soumission du formulaire.');
    });
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

// Appel de la fonction pour charger les données au chargement de la page
window.onload = function () {
    audit_ids.forEach(list_id => {
        loadData(apiUrl, list_id);
    })
};