$(document).ready(function(){
    $('.js-chart').each(function(i, div) {
        var data = $(div).data('chart');
        var ctx = $(div).find('canvas')[0].getContext('2d');
        var chart = new Chart(ctx, data);
    });
});
