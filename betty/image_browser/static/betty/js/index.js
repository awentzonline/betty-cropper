$('#scroll').infinitescroll({
    navSelector     : "#pagination",
    nextSelector    : "a#next",
    itemSelector    : "#scroll li",
    animate         : true,
    donetext        : "End of available images."
},function(){ initPopover(); });

$(window).unbind('.infscr');

$("#next-trigger .btn").click(function(){
    $('#scroll').infinitescroll('retrieve');
    return false;
});

$(document).ajaxError(function (e, xhr, opt) {
    if (xhr.status == 404) $('a#next').remove();
});

$(document).ready(function(){
    initPopover();

    $('#upload-modal').on("loaded.bs.modal", function(e){
        initUploadModal(this);
    });
    $('#upload-modal').on("hidden.bs.modal", function(e){
        clearUploadModal(this);
    });
});

$(document.body).on('click', '#size-select li', function (event) {
    var $t = $(event.currentTarget),
    	l = $(this).find('a');
    $('#size').val(l.attr('data-title'));
	$t.closest('.input-group-btn')
        .find('[data-bind="label"]').text($t.text())
        .end()
        .children('.dropdown-toggle').dropdown('toggle');
    return false;
});

function initPopover() {
    $('#results li a').popover({ 
        html : true,
        content: function() { return $(this).closest('li').find('.details').html(); },
        trigger: 'hover', 
        placement: 'auto',
        delay: { show: 500, hide: 100 },
        title: 'Details'
    });
}