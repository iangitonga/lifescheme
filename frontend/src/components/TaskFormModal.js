import React from "react";
import TaskForm from "./TaskForm";


export default class TaskFormModal extends React.Component {
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
                    <TaskForm
                        closerCallback={this.props.closerCbc}
                        endpoint={this.props.endpoint}
                        newDataCbc={this.newDataCbc}
                        title={this.props.title}
                        submitBtnText={this.props.submitBtnText}/>
                </div>
            </div>
        );
    }
}