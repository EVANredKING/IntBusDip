package com.teamcenter.app.repository;

import com.teamcenter.app.model.Nomenclature;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface NomenclatureRepository extends JpaRepository<Nomenclature, Long> {
    Optional<Nomenclature> findByInternalCode(String internalCode);
} 