import { useNavigate } from "react-router-dom";

const Dashboard = () => {
    const navigate = useNavigate();

    const handleLogout = () => {
        sessionStorage.removeItem("token");
        navigate("/login");
    };

    return (
        <div className="container d-flex flex-column align-items-center justify-content-center min-vh-100 bg-light">
            <h1 className="display-4 text-primary mb-4">Dashboard protegido 🤨</h1>
            <p className="lead text-secondary mb-5">¡Logueado con éxito!</p>
            <button
                className="btn btn-danger"
                onClick={handleLogout}
            >
                Cerrar sesión
            </button>
        </div>
    );
};

export default Dashboard;