import post from "../utils/network";
// TODO: import constants as *
import {ENDPOINTS, UNEXPECTED_ERROR_MESSAGE} from "../constants/constants";
import React from "react";
import ModalLauncherBtn from "./ModalLauncherBtn";
import FormMessageBar from "./FormMessageBar";
import TaskTableRow from "./TaskTableRow";
import TaskFormModal from "./TaskFormModal";
import TaskUpdateFormModal from "./TaskUpdateFormModal";


export default class TaskTable extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            tasks: [],
            // Used to indicate if tasks are loaded when the page is loaded/refreshed.
            tasksAreLoaded: false,
            tasksLoadingFailed: false,
            taskCreateFormModalIsOpen: false,
            taskUpdateFormModalIsOpen: false,
            taskUpdateFormDisplay: false,
            messageIsOpen: false,
            messageIsSuccess: false,
            messageIsError: false,
            message: '',
            taskUpdateFormModalData: {
                initialStartTimeVal: '',
                initialEndTimeVal: '',
                initialTaskDescVal: '',
                isCreated: false,
                isShown: false,
                taskId: '',
            },
            taskDeleteFormModalData: {
                formIsActive: true,
                formMessage: '',
                formMessageIsShown: false,
                formMessageIsSuccess: false,
                isShown: false,
                taskId: '',
                taskName: '',
            }
        };
        this.addNewTask = this.addNewTask.bind(this);
        this.launcherClickCbc = this.launcherClickCbc.bind(this);
        this.closeTaskFormModal = this.closeTaskFormModal.bind(this);
        this.updateExistingTask = this.updateExistingTask.bind(this);
        this.updateTaskStatus = this.updateTaskStatus.bind(this);
        this.getTaskIdx = this.getTaskIdx.bind(this);
        this.displayMessage = this.displayMessage.bind(this);
        this.launchTaskUpdateModal = this.launchTaskUpdateModal.bind(this);
        this.closeTaskDeleteFormModal = this.closeTaskDeleteFormModal.bind(this);
    }

    componentDidMount() {
        const addTasks = (data) => {
            // TASKS: [{}, {}]
            this.setState({
                tasks: data.TASKS,
                tasksAreLoaded: true,
            });
        };
        const failure = () => {
            this.displayMessage(
                'An error occurred. Try reloading the page or contact the admin.',
                false,
            );
            this.setState({
                tasksAreLoaded: true,
                tasksLoadingFailed: true,
            });
        };
        post(
            ENDPOINTS.TASKS_LIST_ENDPOINT,
            {},
            addTasks,
            failure,
            failure,
            () => {},
        )
    }

    taskSortCompareFn(task1, task2) {
        if (task1.startTime < task2.startTime)
            return -1;
        else if (task1.startTime > task2.startTime)
            return 1;
        else return 0;
    }

    addNewTask(data) {
        const newTask = {
            id: data.taskId,
            startTime: data.taskStartTime,
            endTime: data.taskEndTime,
            desc: data.taskDesc,
            completed: false,
        };
        const newTasks = [...this.state.tasks, newTask];
        newTasks.sort(this.taskSortCompareFn);
        this.setState({
            tasks: newTasks,
        });
    }

    updateExistingTask(data) {
        const idx = this.getTaskIdx(data.taskId);
        if (idx !== null) {
            const tasks = this.state.tasks;
            const targetTask = tasks[idx];
            console.log(targetTask);
            targetTask.startTime = data.taskStartTime;
            targetTask.endTime = data.taskEndTime;
            targetTask.desc = data.taskDesc;
            tasks[idx] = targetTask;
            this.setState({
                tasks: tasks,
            });
        } else {
            this.displayMessage(UNEXPECTED_ERROR_MESSAGE, false);
        }
    }

    launcherClickCbc() {
        this.setState({
            taskCreateFormModalIsOpen: true,
        });
    }

    closeTaskFormModal() {
        this.setState({
            taskCreateFormModalIsOpen: false,
        });
    }

    updateTaskStatus(taskId) {
        const successCallback = () => {
            console.log(`TASKS: ${this.state.tasks[0]}`);
            const idx = this.getTaskIdx(taskId);
            if (idx !== null) {
                const tasks = this.state.tasks;
                const target = tasks.splice(idx, 1)[0];
                target.completed = !target.completed;
                tasks.push(target);
                tasks.sort(this.taskSortCompareFn);
                this.setState({
                    tasks: tasks,
                });
            } else {
                this.displayMessage(UNEXPECTED_ERROR_MESSAGE, false);
            }
        };
        post(
            ENDPOINTS.TASK_STATUS_UPDATE_ENDPOINT,
            {'task_id': taskId},
            successCallback,
            () => {this.displayMessage(UNEXPECTED_ERROR_MESSAGE, false);},
            () => {this.displayMessage(UNEXPECTED_ERROR_MESSAGE, false);},
            () => {},
        );
    }

    displayMessage(message, messageIsSuccess = true) {
        this.setState({
            messageIsOpen: true,
            messageIsSuccess: messageIsSuccess,
            messageIsError: !messageIsSuccess,
            message: message,
        });
        setTimeout(() => {
            this.setState({
                messageIsOpen: false,
                messageIsSuccess: false,
                messageIsError: false,
                message: '',
            });
        }, 6000);
    }

    getTaskIdx(taskId) {
        const tasks = this.state.tasks;
        for (let i = 0; i < tasks.length; ++i) {
            if (tasks[i].id === taskId)
                return i;
        }
        return null;
    }

    launchTaskDeleteModal(taskId) {
        const idx = this.getTaskIdx(taskId);
        if (idx !== null) {
            const targetTask = this.state.tasks[idx];
            const data = this.state.taskDeleteFormModalData;
            data.isShown = true;
            data.taskId = taskId;
            data.taskName = targetTask.desc;
            this.setState({
                taskDeleteFormModalData: data,
            });
        } else {
            console.log(`Error retrieving task with idx: ${idx}`);
        }
    }

    closeTaskDeleteFormModal() {
        const data = this.state.taskDeleteFormModalData;
            data.isShown = false;
            this.setState({
                taskDeleteFormModalData: data,
            });
    }

    closeTaskDeleteFormModalCbc(event) {
        if (event.target.id === 'task-delete-modal')
            this.closeTaskDeleteFormModal();
    }

    submitTaskDeleteForm(event) {
        event.preventDefault();
        const data = this.state.taskDeleteFormModalData;
        data.formMessageIsShown = false;
        data.formIsActive = false;
        this.setState({
            taskDeleteFormModalData: data,
        });
        const formData = {
            task_id: this.state.taskDeleteFormModalData.taskId,
        };
        post(
            ENDPOINTS.TASK_DELETE_ENDPOINT,
            formData,
            this.handleTaskDeleteFormSuccess.bind(this),
            this.handleTaskDeleteFormFailure.bind(this),
            this.handleTaskDeleteFormFailure.bind(this),
            () => {
                const data = this.state.taskDeleteFormModalData;
                data.formIsActive = true;
                this.setState({
                    taskDeleteFormModalData: data,
                });
            },
        );
    }

    handleTaskDeleteFormSuccess(data) {
        const idx = this.getTaskIdx(data.taskId);
        if (idx !== null) {
            const tasks = this.state.tasks;
            tasks.splice(idx, 1);
            this.setState({
                tasks: tasks,
            });
            this.closeTaskDeleteFormModal();
        } else {
            console.log(`Error retrieving task with idx: ${data.taskId}`);
        }
    }

    handleTaskDeleteFormFailure() {
        const data = this.state.taskDeleteFormModalData;
        data.formMessage = UNEXPECTED_ERROR_MESSAGE;
        data.formMessageIsSuccess = false;
        data.formMessageIsShown = true;
        this.setState({
            taskDeleteFormModalData: data,
        });
    }

    launchTaskUpdateModal(taskId) {
        const idx = this.getTaskIdx(taskId);
        if (idx !== null) {
            const targetTask = this.state.tasks[idx];
            const data = this.state.taskUpdateFormModalData;
            data.initialStartTimeVal = targetTask.startTime;
            data.initialEndTimeVal = targetTask.endTime;
            data.initialTaskDescVal = targetTask.desc;
            data.isCreated = true;
            data.isShown = true;
            data.taskId = taskId;
            this.setState({
                taskUpdateFormModalData: data,
            });
        } else {
            console.log(`Error retrieving task with idx: ${idx}`);
        }
    }

    _closeTaskUpdateFormModal() {
        const data = this.state.taskUpdateFormModalData;
        data.isShown = false;
        data.isCreated = false;
        data.taskId = '';
        this.setState({
            taskUpdateFormModalData: data,
        });
    }

    _updateExistingTask(data) {
        const idx = this.getTaskIdx(data.taskId);
        const tasks = this.state.tasks;
        const targetTask = tasks[idx];
        targetTask.startTime = data.taskStartTime;
        targetTask.endTime = data.taskEndTime;
        targetTask.desc = data.taskDesc;
        tasks[idx] = targetTask;
        this.setState({
            tasks: tasks,
        });
    }

    render() {
        return (
            <div className='table-wrapper'>
                <header className="table-wrapper__header">
                    <h1 className="table-wrapper__heading">Today's Schedule</h1>
                    <div className="table-wrapper__header-extra">
                        <ModalLauncherBtn clickCbc={this.launcherClickCbc}/>
                    </div>
                    <FormMessageBar message={this.state.message}
                                    messageIsSuccess={this.state.messageIsSuccess}
                                    messageIsError={this.state.messageIsError}
                                    messageIsShown={this.state.messageIsOpen}/>
                </header>
                <table className="table">
                    <colgroup>
                        <col className="table__col--time"/>
                        <col className="table__col--task"/>
                        <col className="table__col--status"/>
                    </colgroup>
                    <thead>
                    <tr className="table__header-row">
                        <th className="table__head">Time</th>
                        <th className="table__head table__head--task">Task</th>
                        <th className="table__head">#</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr className={`table__row ${this.state.tasks.length ? 'table__row--default' : ''}`}>
                        <td className="table__cell" colSpan={'3'} style={{textAlign: 'center'}}>
                            <div className={
                                `loader ${!this.state.tasksAreLoaded ? 'loader--shown' : ''}`
                            }>
                                Loading tasks <div className={'loader__spinner'}/>
                            </div>
                            <span className={`${this.state.tasksAreLoaded && !this.state.tasksLoadingFailed && !this.state.tasks.length ? '' : 'display-none'}`}>
                                You have no saved tasks for today's schedule.
                            </span>
                        </td>
                    </tr>
                    {
                        this.state.tasks.map((task) => {
                            return <TaskTableRow
                                completed={task.completed}
                                desc={task.desc}
                                endTime={task.endTime}
                                key={task.startTime}
                                taskId={task.id}
                                taskStatusUpdateCbc={this.updateTaskStatus}
                                taskUpdateModalLaunchCbc={this.launchTaskUpdateModal}
                                taskDeleteModalLaunchCbc={this.launchTaskDeleteModal.bind(this)}
                                startTime={task.startTime}/>
                        })
                    }
                    </tbody>
                </table>
                <TaskFormModal
                    closerCbc={this.closeTaskFormModal}
                    endpoint={ENDPOINTS.TASK_CREATE_ENDPOINT}
                    id={'task-create-modal'}
                    isOpened={this.state.taskCreateFormModalIsOpen}
                    newDataCbc={this.addNewTask}
                    title={'Create new task'}
                    submitBtnText={'Create'}/>
                {
                    this.state.taskUpdateFormModalData.isCreated ?
                        <TaskUpdateFormModal
                            closerCbc={this._closeTaskUpdateFormModal.bind(this)}
                            endpoint={ENDPOINTS.TASK_UPDATE_ENDPOINT}
                            id={'task-update-modal'}
                            isOpened={this.state.taskUpdateFormModalData.isShown}
                            newDataCbc={this._updateExistingTask.bind(this)}
                            taskId={this.state.taskUpdateFormModalData.taskId}
                            title={'Update Task'}
                            initialStartTimeVal={this.state.taskUpdateFormModalData.initialStartTimeVal}
                            initialEndTimeVal={this.state.taskUpdateFormModalData.initialEndTimeVal}
                            initialTaskDescVal={this.state.taskUpdateFormModalData.initialTaskDescVal}
                            submitBtnText={'Update'}/>
                    : null
                }
                <div className={`modal ${ this.state.taskDeleteFormModalData.isShown ? 'modal--open'  : ''}`}
                     onClick={this.closeTaskDeleteFormModalCbc.bind(this)}
                     id={'task-delete-modal'}>
                    <div className="modal__body js-modal-body">
                        <form className={`form  ${this.state.taskDeleteFormModalData.formIsActive ? '' : 'form--inactive'}`}
                              id={'task-delete-modal'}
                              method="POST"
                              onSubmit={this.submitTaskDeleteForm.bind(this)}>
                            <header className="form__header js-form-header">
                                <h3 className="form__heading">{'Delete task'}</h3>
                                <span className="modal__close" onClick={this.closeTaskDeleteFormModal}>&times;</span>
                            </header>
                            <FormMessageBar message={this.state.taskDeleteFormModalData.formMessage}
                                            messageIsShown={this.state.taskDeleteFormModalData.formMessageIsShown}
                                            messageIsSuccess={this.state.taskDeleteFormModalData.formMessageIsSuccess}
                                            messageIsError={!this.state.taskDeleteFormModalData.formMessageIsSuccess}/>
                            <div className="form__body">
                                <p style={{fontSize: '1.2rem'}}>Are you sure you want to delete
                                    <span style={{fontWeight: 'bold'}}>
                                        {` ${this.state.taskDeleteFormModalData.taskName}`}
                                    </span> task?
                                </p>
                                <button className="btn btn--red form__submit-btn" type="submit">
                                    Yes, delete
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }
}