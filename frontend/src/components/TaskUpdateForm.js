import TaskForm from "./TaskForm";


export default class TaskUpdateForm extends TaskForm {
    constructor(props) {
        super(props);
        this.state.startTimeVal = props.initialStartTimeVal;
        this.state.endTimeVal = props.initialEndTimeVal;
        this.state.taskDescVal = props.initialTaskDescVal;
    }
}
