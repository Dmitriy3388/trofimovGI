// static/js/icons.js

const Icons = {
    // Material icons
    MATERIAL: 'bi-box-seam',
    MATERIAL_ADD: 'bi-plus-circle',
    MATERIAL_EDIT: 'bi-pencil',
    MATERIAL_DELETE: 'bi-trash',
    MATERIAL_VIEW: 'bi-eye',

    // Operation icons
    OPERATION: 'bi-arrow-left-right',
    RECEIPT: 'bi-arrow-down-circle',
    WRITE_OFF: 'bi-arrow-up-circle',

    // Order icons
    ORDER: 'bi-cart',
    ORDER_ADD: 'bi-cart-plus',

    // Dashboard icons
    DASHBOARD: 'bi-speedometer2',
    PROFILE: 'bi-person',
    ANALYTICS: 'bi-graph-up',

    // Status icons
    SUCCESS: 'bi-check-circle',
    WARNING: 'bi-exclamation-triangle',
    ERROR: 'bi-x-circle',
    INFO: 'bi-info-circle',

    // Action icons
    SEARCH: 'bi-search',
    FILTER: 'bi-funnel',
    SORT: 'bi-arrow-down-up',
    REFRESH: 'bi-arrow-clockwise',
    DOWNLOAD: 'bi-download',
    UPLOAD: 'bi-upload',

    // Navigation icons
    MENU: 'bi-list',
    CLOSE: 'bi-x',
    BACK: 'bi-arrow-left',
    NEXT: 'bi-arrow-right'
};

// Utility function to create icon elements
function createIcon(iconClass, classes = '') {
    const icon = document.createElement('i');
    icon.className = `bi ${iconClass} ${classes}`.trim();
    return icon;
}

// Function to replace emojis with icons
function replaceEmojisWithIcons() {
    const emojiMap = {
        '📊': Icons.ANALYTICS,
        '👁️': Icons.MATERIAL_VIEW,
        '✏️': Icons.MATERIAL_EDIT,
        '📈': Icons.RECEIPT,
        '📉': Icons.WRITE_OFF,
        '✅': Icons.SUCCESS,
        '❌': Icons.ERROR,
        '⚠️': Icons.WARNING,
        '🔄': Icons.REFRESH,
        '🔍': Icons.SEARCH
    };

    document.querySelectorAll('*').forEach(element => {
        if (element.childNodes.length === 1 && element.childNodes[0].nodeType === 3) {
            let text = element.textContent;
            Object.keys(emojiMap).forEach(emoji => {
                if (text.includes(emoji)) {
                    const icon = createIcon(emojiMap[emoji], 'me-1');
                    element.innerHTML = element.innerHTML.replace(emoji, icon.outerHTML);
                }
            });
        }
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    replaceEmojisWithIcons();
});