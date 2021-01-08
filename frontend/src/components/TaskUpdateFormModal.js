import React from "react";
import TaskUpdateForm from "./TaskUpdateForm";


export default class TaskUpdateFormModal extends React.Component {
    constructor(props) {
        super(props);
        this.clickHandler = this.clickHandler.bind(this);
        this.newDataCbc = this.newDataCbc.bind(this);
    }

    clickHandler(event) {
        if (event.target.id === this.props.id)
            this.props.closerCbc();
    }

    newDataCbc(data) {
        this.props.closerCbc();
        this.props.newDataCbc(data);
    }

    render() {
        return (
            <div className={`modal ${ this.props.isOpened ? 'modal--open'  : ''}`}
                 onClick={this.clickHandler} id={this.props.id}>
                <div className="modal__body js-modal-body">
                    <TaskUpdateForm
                        closerCallback={this.props.closerCbc}
                        endpoint={this.props.endpoint}
                        initialStartTimeVal={this.props.initialStartTimeVal}
                        initialEndTimeVal={this.props.initialEndTimeVal}
                        initialTaskDescVal={this.props.initialTaskDescVal}
                        newDataCbc={this.newDataCbc}
                        taskId={this.props.taskId}
                        title={this.props.title}
                        submitBtnText={this.props.submitBtnText}/>
                </div>
            </div>
        );
    }
}
