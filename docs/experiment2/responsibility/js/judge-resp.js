/**
 * a jspsych plugin for responsibility judgments
 *
 */


jsPsych.plugins['judge-resp'] = (function() {

  var plugin = {};

  plugin.info = {
    name: 'judge-resp',
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
      red_name: {
          type: jsPsych.plugins.parameterType.STRING,
          pretty_name: 'Red Name',
          default: ' ',
          description: 'Name of red player',
      },
      blue_name: {
          type: jsPsych.plugins.parameterType.STRING,
          pretty_name: 'Blue Name',
          default: ' ',
          description: 'Name of blue player',
      },
      outcome: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Outcome',
        default: ' ',
        description: '',
      }
    }
  }

  var slider_width = 500;
  var slider_labels = ['not at all', 'very much'];
  var button_label = 'Continue';

  plugin.trial = function(display_element, trial) {
    var names = [red(trial.red_name), blue(trial.blue_name)];

    var html = '<div id="jspsych-html-slider-response-wrapper">';
    html += '<div id="jspsych-html-slider-response-stimulus">';
    html += '<h2>' + trial.title + '</h2>';
    html += '<img src="trials/' + trial.trial + '/full.gif"></img>';
    html += '</div> <br>';

    for(var i = 0; i < names.length; i++) {
      html += "<p> How responsible was " + names[i] + " for the " +
        trial.outcome + '? </p>';
      html += '<div class="jspsych-html-slider-response-container"' +
        'style="position:relative; margin: 0 auto 3em auto; width:' + 
        slider_width + 'px;">';
      html += '<div style="width: 100%;" class="jspsych-html-slider' +
        '-response-response slider-two"';
      html += 'id = "jspsych-html-slider-response-response-' + i + '"></div>';

      html += '<div>';
      for(var j = 0; j < slider_labels.length; j++){
        var width = 100/(slider_labels.length-1);
        var left_offset = (j * (100 /(slider_labels.length - 1))) - (width/2);
        html += '<div style="display: inline-block; position: absolute; left:'+left_offset+'%; text-align: center; width: '+width+'%; margin-top: 0.4em;">';
        html += '<span style="text-align: center; font-size: 80%;">'+slider_labels[j]+'</span>';
        html += '</div>';
      }
    
      html += '</div>;
      html += '</div>'; // for response container

    }

    html += '</div>'; // for response wrapper

    // add submit button
    html += '<button id="jspsych-html-slider-response-next" style="margin: 0 1em 3em 1em;" class="jspsych-btn" disabled>'+button_label+'</button>';

    display_element.innerHTML = html;

    var response = {};

    set_slider();

    display_element.querySelector('#jspsych-html-slider-response-next').addEventListener('click', function() {
      for(var i = 0; i < names.length; i++) {
        response[i] = $('#jspsych-html-slider-response-response-'+i).slider('option', 'value');
      }
      end_trial();
    });

    function end_trial(){

      jsPsych.pluginAPI.clearAllTimeouts();

      // save data
      var trialdata = {
        "trial": trial.trial,
        "resp_red": response[0],
        "resp_blue": response[1]
      };

      display_element.innerHTML = '';

      // next trial
      jsPsych.finishTrial(trialdata);
    }

  };

  return plugin;
})();
