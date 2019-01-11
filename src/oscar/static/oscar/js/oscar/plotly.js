$(document).ready(function(){
   $('.plotly-chart').each(function(i, e) {
       Plotly.newPlot(e, $(e).data('series'), $(e).data('layout'));
   });
});
