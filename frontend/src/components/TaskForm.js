import React from 'react';
import FormMessageBar from "./FormMessageBar";
import post from "../utils/network";


export default class TaskForm extends React.Component {
    constructor(props) {
        super(props);
        this.endpoint = props.endpoint;
        this.state = {
            formIsActive: true,
            formMessageIsShown: false,
            formMessageIsSuccess: false,
            formMessageIsError: false,
            formMessage: '',
            startTimeVal: '',
            endTimeVal: '',
            taskDescVal: '',
            startTimeErrMsg: '',
            endTimeErrMsg: '',
            taskDescErrMsg: '',
        };
        this.handleStartTimeChange = this.handleStartTimeChange.bind(this);
        this.handleEndTimeChange = this.handleEndTimeChange.bind(this);
        this.handleTaskChange = this.handleTaskChange.bind(this);
        this.submitForm = this.submitForm.bind(this);
        this.clearFormErrors = this.clearFormErrors.bind(this);
        this.showFormSpinner = this.showFormSpinner.bind(this);
        this.hideFormSpinner = this.hideFormSpinner.bind(this);
        this.handleFormSubmissionSuccess = this.handleFormSubmissionSuccess.bind(this);
        this.handleFormSubmissionFormErrors = this.handleFormSubmissionFormErrors.bind(this);
        this.handleFormSubmissionFailure = this.handleFormSubmissionFailure.bind(this);
        this.showFormMessage = this.showFormMessage.bind(this);
        this.hideFormMessageBar = this.hideFormMessageBar.bind(this);
    }

    handleStartTimeChange(event) {
        this.setState({startTimeVal: event.target.value});
    }

    handleEndTimeChange(event) {
        this.setState({endTimeVal: event.target.value});
    }

    handleTaskChange(event) {
        this.setState({taskDescVal: event.target.value});
    }

    submitForm(event) {
        event.preventDefault();
        this.hideFormMessageBar();
        this.clearFormErrors();
        this.showFormSpinner();
        const data = {
            start_time: this.state.startTimeVal,
            end_time: this.state.endTimeVal,
            task_desc: this.state.taskDescVal,
            task_id: this.props.taskId,
        };
        post(
            this.endpoint,
            data,
            this.handleFormSubmissionSuccess,
            this.handleFormSubmissionFormErrors,
            this.handleFormSubmissionFailure,
            this.hideFormSpinner,
        );
    }

    clearFormErrors() {
        this.setState({
            startTimeErrMsg: '',
            endTimeErrMsg: '',
            taskDescErrMsg: '',
        });
    }

    showFormSpinner() {
        this.setState({
            formIsActive: false,
        });
    }

    hideFormSpinner() {
        this.setState({
            formIsActive: true,
        });
    }

    handleFormSubmissionSuccess(data) {
        this.props.newDataCbc(data);
        this.setState({
            startTimeVal: '',
            endTimeVal: '',
            taskDescVal: '',
        });
    }

    handleFormSubmissionFormErrors(formErrors) {
        for (const key in formErrors) {
            if (!formErrors.hasOwnProperty(key)) {continue;}
            let error = '';
            for (let i = 0; i < formErrors[key].length; i++) {
                error += formErrors[key][i];
            }
            if (key === 'start_time')
                this.setState({'startTimeErrMsg': error});
            else if (key === 'end_time')
                this.setState({'endTimeErrMsg': error});
            else if (key === 'task_desc')
                this.setState({'taskErrMsg': error});
        }
    }

    handleFormSubmissionFailure() {
        console.log('Failure.');
        this.showFormMessage('An unexpected error occurred. Please try again.', false);
    }

    showFormMessage(message, isSuccess=true) {
        if (isSuccess)
            this.setState({
                formMessageIsSuccess: true,
            });
        else
            this.setState({
                formMessageIsError: true,
            });
        this.setState({
            formMessageIsShown: true,
            formMessage: message,
        });
    }

    hideFormMessageBar() {
        this.setState({
            formMessageIsSuccess: false,
            formMessageIsError: false,
            formMessageIsShown: false,
            formMessage: '',
        });
    }

    render() {
        return (
            <form action={this.endpoint} method="POST" onSubmit={this.submitForm}
                  className={`form  ${this.state.formIsActive ? '' : 'form--inactive'}`}>
                <header className="form__header js-form-header">
                    <h3 className="form__heading">{this.props.title}</h3>
                    <span
                        className="modal__close"
                        onClick={this.props.closerCallback}>
                        &times;
                    </span>
                </header>
                <FormMessageBar
                    message={this.state.formMessage}
                    messageIsShown={this.state.formMessageIsShown}
                    messageIsSuccess={this.state.formMessageIsSuccess}
                    messageIsError={this.state.formMessageIsError}
                />
                <div className="form__body">
                    <div className="form__input-group">
                        <label className="form__input-label">Start time</label>
                        <input
                            className={`form__input ${this.state.startTimeErrMsg ? 'form__input--error ' : ''}`}
                            id="id_start_time"
                            onChange={this.handleStartTimeChange}
                            required
                            type="time"
                            value={this.state.startTimeVal}
                        />
                        <div className="form__input-error-wrapper">
                            <small>{this.state.startTimeErrMsg}</small>
                        </div>
                    </div>
                    <div className="form__input-group">
                        <label className="form__input-label">End time</label>
                        <input id="id_end_time" type="time"
                               className={`form__input ${this.state.endTimeErrMsg ? 'form__input--error ' : ''}`}
                               value={this.state.endTimeVal}
                               onChange={this.handleEndTimeChange} required/>
                        <div className="form__input-error-wrapper">
                            <small>{this.state.endTimeErrMsg}</small>
                        </div>
                    </div>
                    <div className="form__input-group">
                        <label className="form__input-label">Task</label>
                        <input id="id_task" type="text"
                               className={`form__input ${this.state.taskDescErrMsg ? 'form__input--error ' : ''}`}
                               value={this.state.taskDescVal}
                               onChange={this.handleTaskChange} required/>
                        <div className="form__input-error-wrapper">
                            <small>{this.state.taskDescErrMsg}</small>
                        </div>
                    </div>
                    <button className="btn form__submit-btn" type="submit">{this.props.submitBtnText}</button>
                </div>
            </form>
        );
    }
}
