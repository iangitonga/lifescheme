import React from "react";
import TaskStatusCheckbox from "./TaskStatusCheckbox";


export default class TaskTableRow extends React.Component {
    constructor(props) {
        super(props);
        this.taskStatusUpdateCbc = this.taskStatusUpdateCbc.bind(this);
        this.taskDropdownClickHandler = this.taskDropdownClickHandler.bind(this);
        this.state = {
            taskDropdownShown: false,
        };
        this.launchTaskUpdateModal = this.launchTaskUpdateModal.bind(this);
    }

    taskStatusUpdateCbc() {
        this.props.taskStatusUpdateCbc(this.props.taskId);
    }

    taskDropdownClickHandler() {
        this.setState({
            taskDropdownShown: true,
        });
    }

    launchTaskUpdateModal() {
        this.setState({
            taskDropdownShown: false,
        });
        this.props.taskUpdateModalLaunchCbc(this.props.taskId);
    }

    launchTaskDeleteModal() {
        this.setState({
            taskDropdownShown: false,
        });
        this.props.taskDeleteModalLaunchCbc(this.props.taskId);
    }

    render() {
        return (
            <tr className="table__row">
                <td className="table__cell table__cell--time">{`${this.props.startTime} - ${this.props.endTime}`}</td>
                <td className="table__cell table__cell--task">{this.props.desc}</td>
                <td className="table__cell table__cell--status">
                    <TaskStatusCheckbox checked={this.props.completed} taskStatusUpdateCbc={this.taskStatusUpdateCbc}/>
                    <div className="task-dropdown">
                        <button className="task-dropdown__launcher" onClick={this.taskDropdownClickHandler}>
                            <svg className="task-dropdown__svg" focusable="false" xmlns="http://www.w3.org/2000/svg"
                                 viewBox="-1 -2 25 25" height="30px" width="30px">
                                <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                            </svg>
                        </button>
                        <div className={`task-dropdown__content ${this.state.taskDropdownShown ? 'task-dropdown__content--shown' : ''}`}>
                            <button className="task-dropdown__btn" onClick={this.launchTaskUpdateModal}>
                                Edit
                            </button>
                            <button className="task-dropdown__btn" onClick={this.launchTaskDeleteModal.bind(this)}>
                                Delete
                            </button>
                        </div>
                    </div>
                </td>
            </tr>
        );
    }
}