 /**
 * a jspsych plugin for a free response text box
 * 
 *
 * @author Josh de Leeuw
 * (with edits by Shruti)
 */


jsPsych.plugins['free-response'] = (function() {

    var plugin = {};

    plugin.info = {
        name: 'free-response',
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
            outcome_verb: {
                type: jsPsych.plugins.parameterType.STRING,
                pretty_name: 'Outcome Verb',
                default: 'succeed',
                description: 'Succeed or fail',
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
        },
    }


    plugin.trial = function(display_element, trial) {

        var html = "";

        // formulate question and textbox format
        trial.questions = [
            {
              prompt: "Why did " + red(trial.red_name) + " " + trial.outcome_verb + "?",
              rows: 5,
              columns: 50,
              placeholder: "Your response",
            }
        ];

        // start form
        html += '<form id="jspsych-survey-text-form" autocomplete="off">';

        // display trial
        html += '<h2>' + trial.title + '</h2>';
        html += '<img src="trials/' + trial.trial + '/full.gif"> </img>';
        html += '<p> Players: ' + red(trial.red_name) + ', ' + 
            blue(trial.blue_name) + '</p> </div>';

        // add questions
        for (var i = 0; i < trial.questions.length; i++) {
            var question = trial.questions[i];
            html +=
                '<div id="jspsych-survey-text-' + i +
                '" class="jspsych-survey-text-question" style="margin: 2em 0em;">';
            html += '<p class="jspsych-survey-text">' + question.prompt + "</p>";
            var autofocus = i == 0 ? "autofocus" : "";
            html +=
                    '<textarea id="input-' + i +
                    '" name="#jspsych-survey-text-response-' + i +
                    '" cols="' + question.columns +
                    '" rows="' + question.rows +
                    '" ' +
                    autofocus +
                    " required " +
                    ' placeholder="' + question.placeholder +
                    '"></textarea>';

            html += "</div>";
        }

        // add submit button
        html += '<input type="submit" id="jspsych-survey-text-next" class=' +
            '"jspsych-btn jspsych-survey-text" value="Continue"></input>';

        html += "</form>";
        display_element.innerHTML = html;

        display_element.querySelector("#jspsych-survey-text-form").addEventListener("submit", (e) => {
            e.preventDefault();
            var response = {};

            for (var index = 0; index < trial.questions.length; index++) {
                var id = "Q" + index;
                var q_element = document
                    .querySelector("#jspsych-survey-text-" + index)
                    .querySelector("textarea, input");
                response = q_element.value;
            }

            // save response data
            var trialdata = {
                "trial": trial.trial,
                "response": response
            };

            display_element.innerHTML = "";

            // next trial
            jsPsych.finishTrial(trialdata);
        });

    };

    return plugin;

})();
