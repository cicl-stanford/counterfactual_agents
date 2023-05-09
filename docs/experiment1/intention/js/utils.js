red = '<b><span style="color:rgb(255,60,60);">red</span></b>';
blue = '<b><span style="color:rgb(0,170,255);">blue</span></b>';

function set_slider() {
    $('.jspsych-html-slider-response-response').slider();
    
    // hide all slider handles
    $('.ui-slider-handle').hide();

    // show pips
    $('.jspsych-html-slider-response-response').slider({ min: 0, max: 100 })
    $('.slider-three').slider('pips', { first: 'pip', last: 'pip', step: 50 });
    $('.slider-two').slider('pips', { first: 'pip', last: 'pip', step: 100 });

    $('.jspsych-html-slider-response-response').slider().on('slidestart', function( event, ui ) {
        // show handle
        $(this).find('.ui-slider-handle').show();
        $('#jspsych-html-slider-response-next').prop('disabled', false);
        $('#jspsych-instructions-next').prop('disabled', false);
    });
}

function shuffle(array) {
  var currentIndex = array.length, temporaryValue, randomIndex;

  // While there remain elements to shuffle...
  while (0 !== currentIndex) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    // And swap it with the current element.
    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  return array;
}

function range(start, end) {
  // includes start, excludes end
  return new Array(end - start).fill().map((d, i) => i + start);
}

function generate_trial_order(num_trials) {
    return shuffle(range(0, num_trials))
}
