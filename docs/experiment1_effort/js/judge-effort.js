/**
 * a jspsych plugin for effort judgments
 *
 */


jsPsych.plugins['judge-effort'] = (function() {

  var plugin = {};

  plugin.info = {
    name: 'judge-effort',
    description: '',
    parameters: {
      trial: {
        type: jsPsych.plugins.parameterType.HTML_STRING,
        pretty_name: 'Trial',
        default: null,
        description: 'Trial number'
      },
      title: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Title',
        default: ' ',
        description: '',
      },
    }
  }

  var slider_width = 500;
  var slider_labels = ['very little', 'very much'];
  var button_label = 'Continue';

  plugin.trial = function(display_element, trial) {

    var html = '<div id="jspsych-html-slider-response-wrapper">';
    html += '<div id="jspsych-html-slider-response-stimulus">';
    html += '<h2>' + trial.title + '</h2>';
    html += '<img src="trials/' + trial.trial + '/full.gif"></img></div>';
    html += '<p> How much effort was the blue player exerting? </p>';
    html += '<div class="jspsych-html-slider-response-container" style="position:relative; margin: 0 auto 2em auto; width:' + slider_width + 'px;">';

    html += '<div style="width: 100%;" class="jspsych-html-slider-response-response slider-two"></div>';
    html += '<div>'
    for(var j=0; j < slider_labels.length; j++){
      var width = 100/(slider_labels.length-1);
      var left_offset = (j * (100 /(slider_labels.length - 1))) - (width/2);
      html += '<div style="display: inline-block; position: absolute; left:'+left_offset+'%; text-align: center; width: '+width+'%; margin-top: 0.4em;">';
      html += '<span style="text-align: center; font-size: 80%;">'+slider_labels[j]+'</span>';
      html += '</div>'
    }
    html += '</div>'; // for response container
    html += '</div>'; // for response wrapper
    html += '</div>';

    // add submit button
    html += '<button id="jspsych-html-slider-response-next" style="margin: 0 1em 3em 1em;" class="jspsych-btn" disabled>'+button_label+'</button>';

    display_element.innerHTML = html;

    var response = {};

    set_slider();

    display_element.querySelector('#jspsych-html-slider-response-next').addEventListener('click', function() {
      response.slider = $('.jspsych-html-slider-response-response').slider('option', 'value');
      end_trial();
    });

    function end_trial(){

      jsPsych.pluginAPI.clearAllTimeouts();

      // save data
      var trialdata = {
        "trial": trial.trial,
        "response": response.slider
      };

      display_element.innerHTML = '';

      // next trial
      jsPsych.finishTrial(trialdata);
    }

  };

  return plugin;
})();
